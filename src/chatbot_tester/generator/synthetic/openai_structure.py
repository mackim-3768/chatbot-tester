from __future__ import annotations

import hashlib
import json
import os
import random
import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple

from openai import OpenAI

from ..schema import sample_schema
from ..types import Message, TestSample
from ..utils import ensure_dir, gen_id_from_messages, now_iso
from ..writers import build_metadata, write_jsonl, write_metadata

# New imports for backend integration
import asyncio
from ...runner.backends.base import backend_registry
from ...runner.models import RunRequest, RunConfig, DatasetInfo, TestSample as RunnerSample, Message as RunnerMessage
from ...runner.runner_context import RunnerContext


# -----------------------------------------------------------------------------
# Data model & configuration types
# -----------------------------------------------------------------------------


@dataclass
class StructureSpec:
    """Specification of the synthetic sample structure.

    v0: single-turn conversation with optional system and expected answer.
    """

    id: str
    turns: int
    include_system: bool
    include_expected: bool
    min_user_len: int
    max_user_len: int
    min_expected_len: int
    max_expected_len: int


@dataclass
class RuleResult:
    rule_id: str
    passed: bool
    message: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None


class SampleRule(Protocol):
    def __call__(self, sample: TestSample) -> RuleResult:  # pragma: no cover - protocol
        ...


@dataclass
class QualityProfile:
    id: str
    language_code: str
    sample_rules: List[SampleRule]


class CacheStrategy(str, Enum):
    DEFAULT = "default"   # reuse if spec_hash matches
    OVERWRITE = "overwrite"  # ignore cache and overwrite outputs
    IGNORE = "ignore"     # ignore cache when reading, but still write manifest


# -----------------------------------------------------------------------------
# Default structure spec (single preset)
# -----------------------------------------------------------------------------


def get_default_structure_spec() -> StructureSpec:
    """Return the default structure spec for everyday conversations.

    - Single-turn user → assistant
    - With system prompt
    - With expected answer
    - Reasonable character-length bounds
    """

    return StructureSpec(
        id="everyday_conversation_basic",
        turns=1,
        include_system=True,
        include_expected=True,
        min_user_len=10,
        max_user_len=200,
        min_expected_len=20,
        max_expected_len=400,
    )


# -----------------------------------------------------------------------------
# Language & length quality rules (multilingual-friendly, heuristic-based)
# -----------------------------------------------------------------------------


_HANGUL_RE = re.compile(r"[가-힣]")
_HIRAGANA_RE = re.compile(r"[ぁ-ゟ]")
_KATAKANA_RE = re.compile(r"[゠-ヿ]")
_LATIN_RE = re.compile(r"[A-Za-z]")


def _text_for_language_checks(sample: TestSample) -> str:
    parts: List[str] = [m.content for m in sample.messages]
    exp = sample.expected
    if isinstance(exp, str):
        parts.append(exp)
    return "\n".join(parts)


def _is_probably_language(text: str, language_code: str) -> bool:
    """Very lightweight heuristic language check.

    This is intentionally simple and conservative; it is not a full
    language detector, just a basic safety net for obvious mismatches.
    """

    if not text.strip():
        return True

    if language_code == "en":
        has_latin = bool(_LATIN_RE.search(text))
        has_hangul = bool(_HANGUL_RE.search(text))
        # Accept if there is some latin and not dominated by hangul-only text.
        return has_latin and not has_hangul

    if language_code == "ko":
        return bool(_HANGUL_RE.search(text))

    if language_code == "ja":
        return bool(_HIRAGANA_RE.search(text) or _KATAKANA_RE.search(text))

    # For other languages, do not enforce for now.
    return True


def make_language_rule(language_code: str) -> SampleRule:
    rule_id = f"lang_{language_code}"

    def _rule(sample: TestSample) -> RuleResult:
        text = _text_for_language_checks(sample)
        ok = _is_probably_language(text, language_code)
        msg = None if ok else f"text does not look like language={language_code}"
        return RuleResult(rule_id=rule_id, passed=ok, message=msg)

    return _rule


def make_length_rule(spec: StructureSpec) -> SampleRule:
    rule_id = "length_bounds"

    def _rule(sample: TestSample) -> RuleResult:
        user_len = sum(len(m.content) for m in sample.messages if m.role == "user")
        expected_text = sample.expected if isinstance(sample.expected, str) else ""
        expected_len = len(expected_text)

        ok = True
        if spec.min_user_len is not None and user_len < spec.min_user_len:
            ok = False
        if spec.max_user_len is not None and user_len > spec.max_user_len:
            ok = False
        if spec.include_expected:
            if spec.min_expected_len is not None and expected_len < spec.min_expected_len:
                ok = False
            if spec.max_expected_len is not None and expected_len > spec.max_expected_len:
                ok = False

        msg = None if ok else f"user_len={user_len}, expected_len={expected_len} out of bounds"
        return RuleResult(rule_id=rule_id, passed=ok, message=msg)

    return _rule


def get_quality_profile(language_code: str, spec: StructureSpec) -> QualityProfile:
    """Return a simple quality profile for the given language.

    v0: only length + heuristic language checks. No sensitive-content rules yet.
    """

    rules: List[SampleRule] = [
        make_language_rule(language_code),
        make_length_rule(spec),
    ]
    return QualityProfile(
        id=f"everyday_{language_code}_default",
        language_code=language_code,
        sample_rules=rules,
    )


def apply_quality_profile(sample: TestSample, profile: QualityProfile) -> Tuple[bool, List[RuleResult]]:
    results: List[RuleResult] = []
    for rule in profile.sample_rules:
        r = rule(sample)
        results.append(r)
        if not r.passed:
            return False, results
    return True, results


# -----------------------------------------------------------------------------
# Caching helpers (filesystem-based, no DB)
# -----------------------------------------------------------------------------


def _build_spec_hash(
    *,
    dataset_id: str,
    version: str,
    topic_prompt: str,
    language_code: str,
    sample_count: int,
    model: str,
    structure_spec: StructureSpec,
    seed: Optional[int],
) -> str:
    payload = {
        "dataset_id": dataset_id,
        "version": version,
        "topic_prompt": topic_prompt,
        "language_code": language_code,
        "sample_count": sample_count,
        "model": model,
        "structure_spec": asdict(structure_spec),
        "seed": seed,
    }
    s = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _load_cache_if_valid(out_root: Path, spec_hash: str, strategy: CacheStrategy) -> Optional[Path]:
    if strategy is not CacheStrategy.DEFAULT:
        return None

    manifest_path = out_root / "cache_manifest.json"
    test_path = out_root / "test.jsonl"
    meta_path = out_root / "metadata.json"
    schema_path = out_root / "schema.json"

    if not (manifest_path.exists() and test_path.exists() and meta_path.exists() and schema_path.exists()):
        return None

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    if data.get("spec_hash") != spec_hash:
        return None

    return out_root


def _write_cache_manifest(
    out_root: Path,
    *,
    spec_hash: str,
    dataset_id: str,
    version: str,
) -> None:
    manifest_path = out_root / "cache_manifest.json"
    payload = {
        "dataset_id": dataset_id,
        "version": version,
        "spec_hash": spec_hash,
        "created_at": now_iso(),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# -----------------------------------------------------------------------------
# Backend-agnostic generation
# -----------------------------------------------------------------------------


def _build_system_prompt(language_code: str) -> str:
    return (
        "You are a data generator that creates evaluation datasets for chatbots. "
        "You must strictly follow the requested JSON output format. "
        f"All user queries and answers must be written in natural language for locale '{language_code}'."
    )


def _build_user_prompt(
    topic_prompt: str,
    language_code: str,
    structure_spec: StructureSpec,
    batch_size: int,
) -> str:
    return (
        f"{topic_prompt}\n\n"
        f"Generate {batch_size} independent single-turn user queries and assistant answers "
        f"about everyday life situations in locale '{language_code}'.\n"
        "Return ONLY a JSON array of objects. Do not include any additional text before or after the JSON.\n"
        "Each array element must be an object with the following fields:\n"
        "  - user_utterance: string, the user's message.\n"
        "  - assistant_answer: string, a helpful assistant reply.\n"
        "  - category: string, a coarse topic label such as 'shopping', 'commute', 'dining', 'health', 'finance', etc.\n"
        "  - tags: array of strings, including 'everyday_life', the category, and the language code.\n"
        f"Approximate length constraints (in characters): user_utterance between {structure_spec.min_user_len} and {structure_spec.max_user_len}, "
        f"assistant_answer between {structure_spec.min_expected_len} and {structure_spec.max_expected_len}."
    )


def _request_batch_via_backend(
    *,
    backend: Any,  # ChatBackend
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float,
) -> List[Dict[str, Any]]:
    """Call the backend and parse the result.

    We expect a top-level JSON array, or an object containing an array under
    one of the common keys (items/data/samples).
    """
    
    # Construct RunnerMessage objects
    messages = [
        RunnerMessage(role="system", content=system_prompt),
        RunnerMessage(role="user", content=user_prompt),
    ]
    
    # Create a dummy sample for the request
    # usage of uuid for ID is better but empty string is fine for this transient object
    sample = RunnerSample(id="", messages=messages)
    
    run_config = RunConfig(
        backend=backend.name if hasattr(backend, "name") else "unknown",
        model=model,
        parameters={
            "temperature": temperature,
            "response_format": {"type": "json_object"}, # Hint for OpenAI-compatible backends
        }
    )
    
    dataset_info = DatasetInfo(dataset_id=None, name=None, version=None, source="generator")
    
    request = RunRequest(
        sample=sample,
        run_config=run_config,
        dataset_info=dataset_info,
        trace_id="gen-" + hashlib.md5(user_prompt.encode()).hexdigest(),
        attempt=1,
        timeout_seconds=120.0,
    )
    
    # Execute synchronously for this generator script
    # If there is a running loop, we might need nested handling, but usually this is a script.
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
         # If we are already in an async context, this might be tricky without a proper changes to upstack.
         # For now, assuming this is called from a CLI/script that isn't already inside a loop for generation logic.
         # However, if it IS, we should ideally await. But the signature of generate_structured_synthetic_dataset is sync.
         # We will use a workaround or assume sync context.  
         # Ideally we should make generate_structured_synthetic_dataset async, but that's a breaking change for callers.
         # For this refactor, we'll try to use asyncio.run or loop.run_until_complete if not running.
         # If running, we might fail. Let's assume sync entry point for now.
         pass
         
    # Run the async send
    # Using a fresh loop if needed or asyncio.run which creates one
    try:
        response = asyncio.run(backend.send(request))
    except RuntimeError:
        # Loop already running?
        # This is a common issue. If we are in a notebook or existing loop.
        # But this code seems to be library code.
        # Let's try to just run it.
        # If we are effectively in a sync function, asyncio.run should work.
        pass
        # Fallback if asyncio.run fails due to existing loop (though nest_asyncio might be needed then)
        # For now, standard asyncio.run
        response = asyncio.run(backend.send(request))


    content = response.text or ""
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return []

    if isinstance(parsed, list):
        return [x for x in parsed if isinstance(x, dict)]

    if isinstance(parsed, dict):
        for key in ("items", "data", "samples"):
            val = parsed.get(key)
            if isinstance(val, list):
                return [x for x in val if isinstance(x, dict)]
        return [parsed]

    return []


# -----------------------------------------------------------------------------
# Row → TestSample conversion
# -----------------------------------------------------------------------------


def _row_to_sample(
    row: Dict[str, Any],
    *,
    system_prompt: str,
    language_code: str,
    structure_spec: StructureSpec,
) -> Optional[TestSample]:
    user_text = str(row.get("user_utterance") or "").strip()
    answer_text = str(row.get("assistant_answer") or "").strip()
    category = str(row.get("category") or "").strip() or "general"

    if not user_text:
        return None
    if structure_spec.include_expected and not answer_text:
        return None

    messages: List[Message] = []
    if structure_spec.include_system and system_prompt:
        messages.append(Message(role="system", content=system_prompt))
    messages.append(Message(role="user", content=user_text))

    md: Dict[str, Any] = {
        "language": language_code,
        "topic": "everyday_life",
        "category": category,
        "source": "openai_structure",
    }

    tags = row.get("tags")
    if not isinstance(tags, list):
        tags_list: List[str] = ["everyday_life", category, language_code]
    else:
        tags_list = [str(t) for t in tags]
        base_tags = {"everyday_life", category, language_code}
        tags_list = list(dict.fromkeys(tags_list + list(base_tags)))  # deduplicate while preserving order

    msg_dicts = [m.to_dict() for m in messages]
    sample_id = gen_id_from_messages(msg_dicts)

    expected: Optional[Any]
    if structure_spec.include_expected:
        expected = answer_text
    else:
        expected = None

    return TestSample(
        id=sample_id,
        messages=messages,
        expected=expected,
        tags=tags_list,
        metadata=md,
    )


# -----------------------------------------------------------------------------
# Core generation loop (OpenAI + quality + dedup)
# -----------------------------------------------------------------------------


def _generate_samples_via_backend(
    *,
    topic_prompt: str,
    language_code: str,
    sample_count: int,
    model: str,
    structure_spec: StructureSpec,
    quality_profile: QualityProfile,
    seed: Optional[int],
    backend_name: str,
    backend_options: Dict[str, Any],
) -> List[TestSample]:
    # Initialize backend
    ctx = RunnerContext()
    backend = backend_registry.create(backend_name, context=ctx, **backend_options)
    
    system_prompt = _build_system_prompt(language_code)

    rng = random.Random(seed) if seed is not None else random
    temperature = 0.7

    batch_size = min(20, max(1, sample_count))

    samples: List[TestSample] = []
    fingerprints: set[str] = set()

    # Allow some extra batches to compensate for filtering failures.
    max_batches = max(4, (sample_count // batch_size) + 2)

    for _ in range(max_batches):
        if len(samples) >= sample_count:
            break

        remaining = sample_count - len(samples)
        this_batch = min(batch_size, remaining + 3)  # ask for a few extra

        user_prompt = _build_user_prompt(
            topic_prompt=topic_prompt,
            language_code=language_code,
            structure_spec=structure_spec,
            batch_size=this_batch,
        )

        rows = _request_batch_via_backend(
            backend=backend,
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )

        rng.shuffle(rows)

        for row in rows:
            sample = _row_to_sample(
                row,
                system_prompt=system_prompt,
                language_code=language_code,
                structure_spec=structure_spec,
            )
            if sample is None:
                continue

            ok, _ = apply_quality_profile(sample, quality_profile)
            if not ok:
                continue

            fp_src = _text_for_language_checks(sample)
            fingerprint = hashlib.sha1(fp_src.encode("utf-8")).hexdigest()  # nosec - non-crypto id
            if fingerprint in fingerprints:
                continue
            fingerprints.add(fingerprint)

            samples.append(sample)
            if len(samples) >= sample_count:
                break

    return samples


# -----------------------------------------------------------------------------
# Public entrypoint
# -----------------------------------------------------------------------------


def generate_structured_synthetic_dataset(
    *,
    dataset_id: str,
    name: str,
    version: str,
    topic_prompt: str,
    language_code: str,
    sample_count: int,
    output_dir: Path | str,
    backend_name: str = "openai",
    backend_options: Optional[Dict[str, Any]] = None,
    openai_model: Optional[str] = None, # kept for backward compatibility, mapped to model in backend options if needed
    cache_strategy: CacheStrategy = CacheStrategy.DEFAULT,
    seed: Optional[int] = None,
) -> Path:
    """Generate a synthetic dataset using a ChatBackend (structured JSON output).

    This writes `test.jsonl`, `metadata.json`, and `schema.json` under
    `<output_dir>/<dataset_id>_<version>/` and returns that directory path.
    """

    if sample_count <= 0:
        raise ValueError("sample_count must be positive")

    backend_options = backend_options or {}
    
    # Resolve model
    # If openai_model is passed, prefer it (backwards compat). 
    # Otherwise check env vars or defaults depending on backend.
    
    model = openai_model or backend_options.get("model")
    if not model and backend_name == "openai":
         model = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    
    # If model is found, ensure it's passed to backend options or used in generation
    if model:
        backend_options["model"] = model

    out_dir = Path(output_dir)
    out_root = out_dir / f"{dataset_id}_{version}"

    structure_spec = get_default_structure_spec()
    quality_profile = get_quality_profile(language_code, structure_spec)

    spec_hash = _build_spec_hash(
        dataset_id=dataset_id,
        version=version,
        topic_prompt=topic_prompt,
        language_code=language_code,
        sample_count=sample_count,
        model=model or "default",
        structure_spec=structure_spec,
        seed=seed,
    )

    cached = _load_cache_if_valid(out_root, spec_hash, cache_strategy)
    if cached is not None:
        return cached

    samples = _generate_samples_via_backend(
        topic_prompt=topic_prompt,
        language_code=language_code,
        sample_count=sample_count,
        model=model or "",
        structure_spec=structure_spec,
        quality_profile=quality_profile,
        seed=seed,
        backend_name=backend_name,
        backend_options=backend_options,
    )

    records = [s.to_dict() for s in samples]
    ensure_dir(out_root)

    # test.jsonl
    write_jsonl(records, out_root / "test.jsonl")

    # metadata.json
    filters: Dict[str, Any] = {
        "language": language_code,
        "min_user_len": structure_spec.min_user_len,
        "max_user_len": structure_spec.max_user_len,
        "min_expected_len": structure_spec.min_expected_len,
        "max_expected_len": structure_spec.max_expected_len,
    }

    sampling: Dict[str, Any] = {
        "sample_count_requested": sample_count,
        "sample_count_actual": len(records),
        "batch_size": min(20, max(1, sample_count)),
        "model": model,
        "temperature": 0.7,
        "seed": seed,
        "cache_strategy": cache_strategy.value,
    }

    source: Dict[str, Any] = {
        "type": "synthetic",
        "provider": "openai",
        "method": "chat_completions_json",  # uses response_format={"type": "json_object"}
        "topic_prompt": topic_prompt,
        "language_code": language_code,
        "structure_spec": asdict(structure_spec),
        "quality_profile": quality_profile.id,
    }

    # Any directory inside the git repo works for commit detection.
    repo_dir = Path(__file__).resolve().parents[2]

    meta = build_metadata(
        dataset_id=dataset_id,
        name=name,
        version=version,
        source=source,
        samples=records,
        filters=filters,
        sampling=sampling,
        repo_dir=repo_dir,
    )
    write_metadata(meta, out_root / "metadata.json")

    # schema.json
    with (out_root / "schema.json").open("w", encoding="utf-8") as f:
        json.dump(sample_schema(), f, ensure_ascii=False, indent=2)

    # cache manifest for future reuse
    _write_cache_manifest(
        out_root,
        spec_hash=spec_hash,
        dataset_id=dataset_id,
        version=version,
    )

    return out_root

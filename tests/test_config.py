import tempfile
from pathlib import Path

import pytest
import yaml

from lm_eval_so.config import TesterConfig, GeneratorConfig, RunnerConfig, StructureConfig

def test_load_empty_config(tmp_path):
    config_file = tmp_path / "empty_config.yaml"
    config_file.write_text("{}", encoding="utf-8")
    
    config = TesterConfig.load(str(config_file))
    assert config.generator is None
    assert config.runner is None
    assert config.evaluator is None

def test_load_full_config(tmp_path):
    data = {
        "generator": {
            "dataset_id": "test_ds",
            "topic_prompt": "hello",
            "structure": {
                "turns": 2
            }
        },
        "runner": {
            "max_concurrency": 5
        },
        "evaluator": {
            "metrics": [{"type": "length_check"}]
        }
    }
    config_file = tmp_path / "full_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(data, f)

    config = TesterConfig.load(str(config_file))
    
    assert config.generator is not None
    assert config.generator.dataset_id == "test_ds"
    assert config.generator.structure.turns == 2
    assert config.runner is not None
    assert config.runner.max_concurrency == 5
    assert config.evaluator is not None
    assert len(config.evaluator.metrics) == 1
    assert config.evaluator.metrics[0].type == "length_check"

def test_structure_config_defaults():
    sc = StructureConfig()
    assert sc.turns == 1
    assert sc.include_system is True

def test_runner_config_defaults():
    rc = RunnerConfig()
    assert rc.max_concurrency == 2
    assert rc.timeout_seconds == 60.0

def test_generator_config_defaults():
    gc = GeneratorConfig(topic_prompt="foo")
    assert gc.language_code == "en"
    assert gc.structure is not None

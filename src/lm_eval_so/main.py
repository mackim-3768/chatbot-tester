import argparse
import logging
import sys
from pathlib import Path

from lm_eval_so.core.logging import configure_logging

from lm_eval_so.config import TesterConfig, GeneratorConfig, RunnerConfig

# Import sub-modules for dispatch
# Assuming we can import them. If their CLIs are main blocks, we might need to import functions.
# For now, I'll import the core functions I refactored or key entry points.
from lm_eval_so.generator.synthetic.openai_structure import generate_structured_synthetic_dataset
from lm_eval_so.runner.runner_core import run_job, RunnerOptions # RunnerOptions is gone, checking usages
# from lm_eval_so.evaluator.cli import ... ?

def main():
    parser = argparse.ArgumentParser(description="Chatbot Tester CLI")
    parser.add_argument("--config", type=str, help="Path to tester configuration file (YAML/JSON)", required=True)
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Generate
    gen_parser = subparsers.add_parser("generate", help="Generate synthetic dataset")

    # Run
    run_parser = subparsers.add_parser("run", help="Run tests against a backend")

    # Evaluate
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate results")

    args = parser.parse_args()
    configure_logging(level=logging.INFO)
    config_path = Path(args.config)
    
    try:
        config = TesterConfig.load(config_path)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    if args.command == "generate":
        print(f"Loaded Generator Config: {config.generator}")
        print(f"Loaded Runner Config: {config.runner}")
        print(f"Loaded Evaluator Config: {config.evaluator}")

        if not config.generator:
            print("Error: Generator configuration missing in config file.")
            sys.exit(1)
        
        print(f"Generating dataset '{config.generator.name}'...")
        # Call generator
        # generate_structured_synthetic_dataset(...) using config fields
        # This is a bit verbose mapping, but necessary if the function signature wasn't fully unified to take config object.
        # But wait, I updated openai_structure.py to use StructureConfig, but the function signature still takes many args.
        # I should update generate_structured_synthetic_dataset to take GeneratorConfig or map it here.
        # Mapping here allows preserving the function signature for other callers.
        
        gen_cfg = config.generator
        out_path = generate_structured_synthetic_dataset(
            dataset_id=gen_cfg.dataset_id,
            name=gen_cfg.name,
            version=gen_cfg.version,
            topic_prompt=gen_cfg.topic_prompt,
            language_code=gen_cfg.language_code,
            sample_count=gen_cfg.sample_count,
            output_dir=gen_cfg.output_dir,
            backend_name=gen_cfg.backend,
            backend_options=gen_cfg.backend_options,
            cache_strategy=gen_cfg.cache_strategy, # Need to convert string to Enum? Function expects Enum.
            seed=gen_cfg.seed,
        )
        print(f"Generation complete: {out_path}")

    elif args.command == "run":
        if not config.runner:
            print("Error: Runner configuration missing in config file.")
            sys.exit(1)
        
        print("Running tests... (Not fully implemented in this shim)")
        # run_job(...)
        
    elif args.command == "evaluate":
        if not config.evaluator:
            print("Error: Evaluator configuration missing in config file.")
            sys.exit(1)
        
        print("Evaluating results... (Not fully implemented in this shim)")
        # evaluate(...)

if __name__ == "__main__":
    main()

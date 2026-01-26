try:
    from lm_eval_so.core.backends import backend_registry
    from lm_eval_so.runner import cli
    from lm_eval_so.generator.synthetic import openai_structure
    print("Imports successful")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")

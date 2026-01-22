try:
    from chatbot_tester.core.backends import backend_registry
    from chatbot_tester.runner import cli
    from chatbot_tester.generator.synthetic import openai_structure
    print("Imports successful")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")

# Chatbot Tester Examples

This directory contains examples demonstrating how to use `lm-eval-so` for various use cases.

## Available Examples

### 1. Quickstart (`quickstart/`)
A basic end-to-end example using a simple QA dataset.
- **Features**: CSV input, default metrics (BLEU, ROUGE), OpenAI backend.
- **Run**: `./quickstart/run_quickstart.sh`

### 2. Multi-turn Chat (`multiturn_chat/`)
Demonstrates how to test multi-turn conversations.
- **Features**: 
    - JSON input with `conversation` history (user/assistant turns).
    - Multi-turn context handling in the runner.
- **Run**: `./multiturn_chat/run_multiturn.sh`

### 3. Custom Metrics (`custom_metric/`)
Demonstrates how to implement and use custom Python metrics via the Plugin system.
- **Features**:
    - Custom Metric implementation (`plugins/keyword_metric.py`).
    - Dynamic plugin loading via CLI `--plugin`.
    - Custom configuration in YAML.
- **Run**: `./custom_metric/run_custom_metric.sh`

## Prerequisites

All examples assume you have set your `OPENAI_API_KEY` environment variable, as they default to using the OpenAI backend with `gpt-4o-mini`.

```bash
export OPENAI_API_KEY="sk-..."
```

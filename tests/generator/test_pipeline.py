import pytest
import json
from pathlib import Path
from chatbot_tester.generator.pipeline import PipelineOptions, run_pipeline

def test_run_pipeline_end_to_end(tmp_path):
    # Setup input file
    input_file = tmp_path / "input.csv"
    input_file.write_text("id,user_input,expected_output\n1,hello,hi\n2,bye,goodbye", encoding="utf-8")

    output_dir = tmp_path / "output"

    opts = PipelineOptions(
        input_path=input_file,
        input_format="csv",
        output_dir=output_dir,
        dataset_id="test_ds",
        name="Test Dataset",
        version="v1",
        source=None,
        id_col="id",
        user_col="user_input",
        expected_col="expected_output",
        system_col=None,
        tags_col=None,
        tags_sep="|",
        language_col=None,
        min_len=None,
        max_len=None,
        sample_size=0,
        sample_random=False,
    )

    result_path = run_pipeline(opts)

    # Verify output structure
    assert result_path.exists()
    assert (result_path / "test.jsonl").exists()
    assert (result_path / "metadata.json").exists()
    assert (result_path / "schema.json").exists()

    # Verify content
    with open(result_path / "test.jsonl", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 2
        data1 = json.loads(lines[0])
        # TestSample structure: {"id": ..., "messages": [{"role": "user", "content": "..."}], "expected": ...}
        assert data1["id"] == "1"
        assert data1["messages"][0]["content"] == "hello"
        assert data1["messages"][0]["role"] == "user"
        assert data1["expected"] == "hi"

        data2 = json.loads(lines[1])
        assert data2["id"] == "2"
        assert data2["messages"][0]["content"] == "bye"

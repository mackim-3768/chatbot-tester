
from pathlib import Path
from unittest.mock import MagicMock, patch
from chatbot_tester.generator.loaders.doc_to_qa import DocToQALoader

def test_doc_to_qa_loader(tmp_path):
    loader = DocToQALoader(api_key="dummy")
    doc_path = tmp_path / "doc.txt"
    doc_path.write_text("This is a sample document.", encoding="utf-8")

    with patch("chatbot_tester.generator.loaders.doc_to_qa.OpenAI") as MockOpenAI:
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = '{"pairs": [{"question": "What is this?", "answer": "A sample document."}]}'
        MockOpenAI.return_value.chat.completions.create.return_value = mock_resp

        samples = loader.load(doc_path, count=1)
        assert len(samples) == 1
        assert samples[0].messages[0].content == "What is this?"
        assert samples[0].expected == "A sample document."


from unittest.mock import MagicMock, patch
from chatbot_tester.generator.transformers.augmenter import ParaphraseAugmenter
from chatbot_tester.common.models import Message, TestSample

def test_paraphrase_augmenter():
    augmenter = ParaphraseAugmenter(api_key="dummy")
    sample = TestSample(
        id="orig",
        messages=[Message(role="user", content="Hello")],
        expected="Hi",
        tags=[]
    )

    with patch("chatbot_tester.generator.transformers.augmenter.OpenAI") as MockOpenAI:
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = '{"variations": ["Hi there", "Greetings"]}'
        MockOpenAI.return_value.chat.completions.create.return_value = mock_resp

        results = augmenter.augment(sample, count=2)
        assert len(results) == 2
        assert results[0].messages[0].content == "Hi there"
        assert results[0].tags == ["augmented"]

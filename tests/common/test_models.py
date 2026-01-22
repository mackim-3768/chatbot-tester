import pytest
from chatbot_tester.common.models import Message, TestSample

def test_message_from_dict():
    data = {"role": "user", "content": "hello"}
    msg = Message.from_dict(data)
    assert msg.role == "user"
    assert msg.content == "hello"
    assert msg.name is None
    assert msg.metadata is None

def test_message_to_dict():
    msg = Message(role="system", content="hi", name="bot", metadata={"a": 1})
    d = msg.to_dict()
    assert d["role"] == "system"
    assert d["content"] == "hi"
    assert d["name"] == "bot"
    assert d["metadata"] == {"a": 1}

def test_testsample_from_dict():
    data = {
        "id": "t1",
        "messages": [{"role": "user", "content": "q"}],
        "expected": "a",
        "tags": ["t1", "t2"],
        "metadata": {"source": "manual"}
    }
    sample = TestSample.from_dict(data)
    assert sample.id == "t1"
    assert len(sample.messages) == 1
    assert sample.messages[0].role == "user"
    assert sample.expected == "a"
    assert sample.tags == ["t1", "t2"]
    assert sample.metadata == {"source": "manual"}

def test_testsample_to_dict():
    msg = Message(role="user", content="q")
    sample = TestSample(
        id="t2",
        messages=[msg],
        expected={"ans": "yes"},
        tags=None,
        metadata=None
    )
    d = sample.to_dict()
    assert d["id"] == "t2"
    assert len(d["messages"]) == 1
    assert d["messages"][0]["content"] == "q"
    assert d["expected"] == {"ans": "yes"}
    assert "tags" not in d
    assert "metadata" not in d

from alinux.agent import Agent


def test_empty_input_returns_safe_response(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = Agent().decide("   ")

    assert result.action == "respond_to_user"
    assert "Please enter" in result.parameter


def test_without_api_key_does_not_call_model(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ALINUX_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    agent = Agent()

    assert agent.local is True
    assert agent.provider == "ollama"
    assert agent.model == "llama3.2:3b"
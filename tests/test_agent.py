from alinux.agent import Agent, AgentAction


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
    assert agent.model == "smollm2:135m"


def test_greeting_bypasses_local_model(monkeypatch):
    monkeypatch.setattr(
        Agent,
        "_local_completion",
        lambda *_args: (_ for _ in ()).throw(AssertionError("model should not be called")),
    )

    result = Agent().decide("hi")

    assert result.action == "respond_to_user"
    assert "ready" in result.parameter


def test_casual_question_does_not_trigger_system_action():
    result = Agent().decide("hello, how are you?")

    assert result.action == "respond_to_user"
    assert "monitoring" in result.parameter


def test_invalid_model_system_command_is_rejected():
    try:
        AgentAction(action="system_command", parameter="cat /proc/stat")
    except ValueError as exc:
        assert "Unsupported system command" in str(exc)
    else:
        raise AssertionError("invalid system command was accepted")
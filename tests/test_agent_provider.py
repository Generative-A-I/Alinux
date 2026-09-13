from alinux.agent import Agent


def test_groq_provider_selects_builtin_model_and_endpoint(monkeypatch):
    monkeypatch.setenv("ALINUX_PROVIDER", "groq")
    monkeypatch.setenv("ALINUX_API_KEY", "test-key")

    agent = Agent()

    assert agent.model == "llama-3.3-70b-versatile"
    assert agent.base_url == "https://api.groq.com/openai/v1"
    assert agent.api_key == "test-key"


def test_custom_openai_compatible_configuration(monkeypatch):
    monkeypatch.delenv("ALINUX_PROVIDER", raising=False)
    monkeypatch.setenv("ALINUX_API_KEY", "custom-key")
    monkeypatch.setenv("ALINUX_API_BASE_URL", "https://example.test/v1")

    agent = Agent(model="local-model")

    assert agent.model == "local-model"
    assert agent.base_url == "https://example.test/v1"
    assert agent.api_key == "custom-key"


def test_default_groq_flag_uses_groq_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "groq-key")

    agent = Agent(use_default_groq_api=True)

    assert agent.provider == "groq"
    assert agent.model == "llama-3.3-70b-versatile"
    assert agent.api_key == "groq-key"
from alinux.agent import Agent


def test_invalid_local_action_retries_as_user_response(monkeypatch):
    responses = iter(
        [
            '{"action":"system_command","parameter":"...","thought":""}',
            '{"action":"respond_to_user","parameter":"The model answer","thought":""}',
        ]
    )
    monkeypatch.setattr(Agent, "_local_completion", lambda self, _text, clarify=False: next(responses))

    result = Agent().decide("what is the capital of France?")

    assert result.action == "respond_to_user"
    assert result.parameter == "The model answer"
import json

from alinux.agent import Agent


def test_local_request_sets_small_generation_budget(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({"message": {"content": "{}"}}).encode()

    def fake_urlopen(request, timeout):
        captured["payload"] = json.loads(request.data)
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    Agent()._local_completion("do something")

    assert captured["payload"]["model"] == "smollm2:135m"
    assert captured["payload"]["options"]["num_predict"] == 96
    assert captured["payload"]["keep_alive"] == "10m"
    assert captured["timeout"] == 180
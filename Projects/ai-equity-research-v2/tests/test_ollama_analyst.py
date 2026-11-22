import io
import json
from unittest.mock import patch

from ollama_analyst import analyze_report


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_analyze_report_uses_structured_indonesian_prompt_and_higher_token_budget():
    captured = {}

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse({"response": "Ringkasan pasar. Prioritas. Risiko. TPIA. Rencana sesi berikutnya.", "done_reason": "stop"})

    with patch("ollama_analyst.urllib.request.urlopen", side_effect=fake_urlopen):
        answer = analyze_report("PANTAUAN KHUSUS TPIA: NO_TRADE, close 1155, RSI 32.9")

    assert "TPIA" in answer
    assert captured["body"]["model"] == "gemma4:latest"
    assert captured["body"]["options"]["num_predict"] >= 500
    assert captured["body"]["options"]["num_ctx"] == 4096
    assert "300–350 token" in captured["body"]["prompt"]
    assert "PANTAUAN KHUSUS TPIA" in captured["body"]["prompt"]

# HTTP (REST) agent example

A chat agent behind one REST endpoint. Each red-team turn is one `POST /chat`; the agent answers with JSON. The field names match the console's defaults, so you only add the URL and the auth header.

## Run it

```bash
pip install -r requirements.txt
export AGENT_API_KEY=choose-a-test-key        # required as a Bearer token; unset = no auth (local only)
uvicorn agent:app --host 127.0.0.1 --port 8080
```

Optional: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` switch from keyword rules to a real model (see the [main README](../README.md#two-modes)).

Try it:

```bash
curl -s http://127.0.0.1:8080/chat \
  -H "Authorization: Bearer $AGENT_API_KEY" -H "Content-Type: application/json" \
  -d '{"message": "What is my balance?", "session_id": "rt-abc123"}'
```

```json
{
  "reply": "Your alice balance: $420.00.",
  "session_id": "rt-abc123",
  "actions": [{"name": "get_balance", "arguments": {"customer": "alice"}}]
}
```

## API

| | |
|-|-|
| Request | `POST /chat`, `Authorization: Bearer <AGENT_API_KEY>`, body `{"message": "...", "session_id": "..."}`. `session_id` is optional; a new one is returned if it is missing. |
| Response | `{"reply": "...", "session_id": "...", "actions": [{"name": "...", "arguments": {...}}]}` |
| Health | `GET /health` returns `{"status": "ok", "mode": "rules"}` or `"llm"` |

## Console settings

In **Agentic Red Teaming → New assessment → 01 Connect**, choose **HTTP endpoint**:

| Field | Value |
|-------|-------|
| **Endpoint URL** | Your public URL plus `/chat`, for example `https://<name>.trycloudflare.com/chat` |
| **Reply path** | `reply` (default) |
| **Session-id path** | `session_id` (default) |
| **Tool-calls path** | `actions` (default) |
| **Request body template** | `{"message": "{{message}}", "session_id": "{{session_id}}"}` (default) |
| **Custom headers** | `Authorization` = `Bearer <AGENT_API_KEY>` |
| **Confirmation replay is safe for this HTTP endpoint** | Can be on: the example has no real side effects |

Click **Test connection**. It should report that the target replied and the reply mapped.

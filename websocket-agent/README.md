# WebSocket agent example

A chat agent behind a WebSocket. The red-team engine connects, optionally sends an opening auth frame, then sends each turn as one frame and reads the agent's reply frames until the reply is finished.

## Run it

```bash
pip install -r requirements.txt
export AGENT_API_KEY=choose-a-test-key        # required as a Bearer token on the handshake
export AGENT_INIT_TOKEN=choose-an-init-token  # optional: require an opening auth frame
python agent.py                               # ws://127.0.0.1:8765
```

| Variable | Default | Effect |
|----------|---------|--------|
| `AGENT_API_KEY` | unset (no auth, local only) | Bearer token required on the handshake |
| `AGENT_INIT_TOKEN` | unset | When set, the first frame must be `{"type": "auth", "token": "<AGENT_INIT_TOKEN>"}` |
| `STREAM` | `1` | `0` sends each reply as one frame instead of streaming it |
| `HOST`, `PORT` | `127.0.0.1`, `8765` | Listen address |
| `TLS_CERT`, `TLS_KEY` | unset | Serve `wss://` directly instead of behind a TLS-terminating tunnel or proxy |
| `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` | unset | Answer with a real model (see the [main README](../README.md#two-modes)) |

## Protocol

All frames are JSON text.

| Direction | Frame |
|-----------|-------|
| handshake | `Authorization: Bearer <AGENT_API_KEY>`; subprotocol `agent.v1` is accepted if offered, but not required |
| agent → engine | `{"type": "ready", "session_id": "..."}` once, right after connecting |
| engine → agent | `{"type": "auth", "token": "..."}` once, only if `AGENT_INIT_TOKEN` is set; answered with `{"type": "ack", ...}` |
| engine → agent | `{"message": "..."}` for each turn |
| agent → engine | `{"type": "typing"}`, then several `{"type": "delta", "text": "..."}`, then `{"type": "complete", "actions": [...]}` |

With `STREAM=0` the reply is a single `{"type": "reply", "reply": "...", "actions": [...]}` frame.

In model mode, a failed model request sends `{"type": "error", "error": "model request failed (HTTP <status>)"}` followed by an empty `complete` (or `reply`) frame, and the connection stays open.

## Console settings

In **Agentic Red Teaming → New assessment → 01 Connect**, choose **WebSocket endpoint**.

**Streamed replies** (default):

| Field | Value |
|-------|-------|
| **WebSocket URL** | Your public URL with `wss://` plus `/chat`, for example `wss://<name>.trycloudflare.com/chat` |
| **Subprotocols** | `agent.v1` (optional) |
| **Opening message** | `{"type": "auth", "token": "<AGENT_INIT_TOKEN>"}`, only if you set `AGENT_INIT_TOKEN` |
| **When is a reply finished?** | **Done marker** |
| **Done path** | `type` |
| **Done value** | `complete` |
| **Join the text of every frame in the reply** | On |
| **Connection** | **Keep the connection open** |
| **Reply path** | `text` |
| **Session-id path** | `session_id` |
| **Tool-calls path** | `actions` |
| **Message template** | `{"message": "{{message}}"}` |
| **Custom headers** | `Authorization` = `Bearer <AGENT_API_KEY>` |

**Single-frame replies** (`STREAM=0`): set **When is a reply finished?** to **First reply message** and **Reply path** to `reply`; leave the done fields empty and joining off.

Click **Test connection**. It should report that the target replied and the reply mapped.

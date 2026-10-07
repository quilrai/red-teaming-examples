"""Run from websocket-agent/: python -m pytest tests"""
import asyncio
import importlib
import json
import sys
from pathlib import Path

import pytest
from websockets.asyncio.client import connect
from websockets.asyncio.server import serve
from websockets.exceptions import InvalidStatus

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def load(monkeypatch, **env):
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    for name in ("AGENT_INIT_TOKEN", "STREAM"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    import agent

    return importlib.reload(agent)


async def turn(agent, message, *, headers=None, subprotocols=None, init=None):
    async with serve(agent.handle, "127.0.0.1", 0, select_subprotocol=agent.select_subprotocol,
                     process_request=agent.check_bearer) as server:
        port = server.sockets[0].getsockname()[1]
        async with connect(f"ws://127.0.0.1:{port}/chat",
                           additional_headers=headers or {"Authorization": "Bearer test-key"},
                           subprotocols=subprotocols) as ws:
            frames = [json.loads(await ws.recv())]
            if init:
                await ws.send(json.dumps(init))
                frames.append(json.loads(await ws.recv()))
            await ws.send(json.dumps({"message": message}))
            while frames[-1].get("type") not in ("complete", "reply", "error"):
                frames.append(json.loads(await asyncio.wait_for(ws.recv(), 5)))
            return ws.subprotocol, frames


def test_streams_a_reply_and_ends_with_the_done_marker(monkeypatch):
    agent = load(monkeypatch)
    subprotocol, frames = asyncio.run(turn(agent, "What is my balance?", subprotocols=["agent.v1"]))
    assert subprotocol == "agent.v1"
    assert frames[0]["type"] == "ready" and frames[0]["session_id"]
    assert frames[1] == {"type": "typing"}
    text = "".join(f["text"] for f in frames if f["type"] == "delta")
    assert text == "Your alice balance: $420.00."
    assert frames[-1] == {"type": "complete", "actions": [{"name": "get_balance", "arguments": {"customer": "alice"}}]}


def test_single_frame_mode_without_a_subprotocol(monkeypatch):
    agent = load(monkeypatch, STREAM="0")
    subprotocol, frames = asyncio.run(turn(agent, "What is my balance?"))
    assert subprotocol is None
    assert frames[-1]["type"] == "reply" and frames[-1]["reply"] == "Your alice balance: $420.00."


def test_rejects_a_wrong_bearer_at_the_handshake(monkeypatch):
    agent = load(monkeypatch)
    with pytest.raises(InvalidStatus):
        asyncio.run(turn(agent, "hi", headers={"Authorization": "Bearer nope"}))


def test_requires_the_auth_frame_when_configured(monkeypatch):
    agent = load(monkeypatch, AGENT_INIT_TOKEN="init-secret")
    _, refused = asyncio.run(turn(agent, "hi"))
    assert refused[-1]["type"] == "error"
    _, frames = asyncio.run(turn(agent, "What is my balance?", init={"type": "auth", "token": "init-secret"}))
    assert frames[1]["authorized"] is True and frames[-1]["type"] == "complete"

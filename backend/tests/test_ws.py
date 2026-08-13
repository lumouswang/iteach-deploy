"""WebSocket 连接 + B4 内存泄漏修复测试。"""
import pytest
from fastapi.testclient import TestClient
from main import app, ws_mgr, room_manager, game_engine


def test_broadcast_cleans_dead_connections(monkeypatch):
    """B4 修复：broadcast() 发送失败应把死连接从 active 列表中清除。"""
    # 注入两个假 ws 到某房间
    fake_room = "fake-room"
    sent = []
    closed = []

    class GoodWS:
        async def send_json(self, msg):
            sent.append(msg)

    class BadWS:
        async def send_json(self, msg):
            raise RuntimeError("client disconnected")
        async def close(self):
            closed.append("closed")

    good = GoodWS()
    bad = BadWS()
    ws_mgr.active[fake_room] = [good, bad]

    import asyncio
    asyncio.get_event_loop().run_until_complete(
        ws_mgr.broadcast(fake_room, {"ok": True})
    )

    # 死连接应被移除，活的还在
    assert good in ws_mgr.active.get(fake_room, [])
    assert bad not in ws_mgr.active.get(fake_room, [])
    # 消息发到了活的
    assert len(sent) == 1
    assert sent[0]["ok"] is True
    # GC：房间里没活连接后，整个 key 被清除
    ws_mgr.disconnect(fake_room, good)
    assert fake_room not in ws_mgr.active


def test_gc_room_when_empty():
    """B4 修复：disconnect 后房间空了，整个 key 被 pop。"""
    ws_mgr.active["room-empty"] = []
    ws_mgr._gc_room("room-empty")
    assert "room-empty" not in ws_mgr.active


def test_disconnect_keeps_other_connections():
    """多连接场景：单独 disconnect 不影响其他 ws。"""
    class WS1: pass
    class WS2: pass
    w1, w2 = WS1(), WS2()
    ws_mgr.active["multi"] = [w1, w2]
    ws_mgr.disconnect("multi", w1)
    assert ws_mgr.active["multi"] == [w2]
    ws_mgr.disconnect("multi", w2)
    assert "multi" not in ws_mgr.active


def test_ws_action_state_in_room():
    """WS action='state' 应正确广播房间状态。"""
    # 先建一个房间，让它存在 room_manager 中
    room = room_manager.create_room("ws-tester")
    game_engine.start_game(room)
    room_id = room.room_id

    # 手动广播一次看 state 字段是否到位
    received = []

    class ListenWS:
        async def send_json(self, msg):
            received.append(msg)

    listener = ListenWS()
    ws_mgr.active[room_id] = [listener]

    import asyncio
    asyncio.get_event_loop().run_until_complete(
        ws_mgr.broadcast(room_id, {"ok": True, "state": room.to_dict()})
    )

    # 清理
    ws_mgr.disconnect(room_id, listener)

    assert len(received) == 1
    msg = received[0]
    assert msg["ok"] is True
    assert msg["state"]["room_id"] == room_id
    assert msg["state"]["phase"] in ("intro", "questioning")

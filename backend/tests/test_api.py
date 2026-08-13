"""端到端 HTTP 测试 — 列了 P0 #1 修复回归 + P1 #10 rejoin/TTL + P2 #14 合并载荷。"""
import time
import pytest


# ============ P0 #1 修复回归：HTTP 端点上不能缺 deck 参数 ============
def test_api_play_card_http_path(client, rm):
    """出牌 HTTP 端点不能传错参数（修复前会抛 TypeError）。"""
    r = client.post("/api/room/create", json={"user_name": "tester"})
    room_id = r.json()["room_id"]
    pid = r.json()["player_id"]
    # 推进到 questioning → 才能出卡
    rm.get_room(room_id).phase = __import__("game.state", fromlist=["GamePhase"]).GamePhase.QUESTIONING
    r = client.post("/api/card/use", json={"room_id": room_id, "card_id": "G1_xuxiake", "player_id": pid})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["clue"]["id"]


def test_api_combo_http_path(client, rm):
    """合技 HTTP 端点不能传错参数。"""
    from game.state import GamePhase
    r = client.post("/api/room/create", json={"user_name": "tester"})
    room_id = r.json()["room_id"]
    pid = r.json()["player_id"]
    room = rm.get_room(room_id)
    room.phase = GamePhase.CARD_PLAY
    # 先出两张参与卡
    client.post("/api/card/use", json={"room_id": room_id, "card_id": "G1_xuxiake", "player_id": pid})
    client.post("/api/card/use", json={"room_id": room_id, "card_id": "G2_shenkuo", "player_id": pid})
    # 合技
    r = client.post("/api/card/combo", json={"room_id": room_id, "cards": ["G1_xuxiake", "G2_shenkuo"], "player_id": pid})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["unlock_layer"] == "phenomenon"


# ============ P0 #5 修复回归：G7 链结合技要求 G7 自己已用过 ============
def test_api_g7_combo_requires_g7_used(client, rm):
    """P0 #5：G7 没出过 → 链结合技被拒绝。"""
    from game.state import GamePhase
    r = client.post("/api/room/multiplayer", json={"user_name": "Alice"})
    room_id = r.json()["room_id"]
    alice = r.json()["player_id"]
    rj = client.post("/api/room/join", json={"room_id": room_id, "user_name": "Bob"})
    bob = rj.json()["player_id"]
    room = rm.get_room(room_id)
    room.phase = GamePhase.CARD_PLAY
    # Alice 出 G7
    client.post("/api/card/use", json={"room_id": room_id, "card_id": "G7_lishizhen", "player_id": alice})
    # Bob 出 G1
    rm.get_room(room_id).turn_player_id = bob
    client.post("/api/card/use", json={"room_id": room_id, "card_id": "G1_xuxiake", "player_id": bob})
    # Alice 回合：合技 G7 + G1 → G7 自己已用过 1 次，应允许
    rm.get_room(room_id).turn_player_id = alice
    r = client.post("/api/card/combo", json={"room_id": room_id, "cards": ["G7_lishizhen", "G1_xuxiake"], "player_id": alice})
    # 前提层未解锁 → 返 400 但不是 "G7 必须先出过"
    assert r.status_code == 400, r.text
    body = r.json()
    # 错误信息应不包含 "G7李时珍必须先出过"
    assert "G7李时珍必须先出过" not in body.get("detail", "")


def test_api_g7_combo_g7_not_used_blocked(client, rm):
    """P0 #5：G7 没出过 → 链结合技被拒绝。"""
    from game.state import GamePhase
    r = client.post("/api/room/multiplayer", json={"user_name": "Alice"})
    room_id = r.json()["room_id"]
    alice = r.json()["player_id"]
    rj = client.post("/api/room/join", json={"room_id": room_id, "user_name": "Bob"})
    bob = rj.json()["player_id"]
    room = rm.get_room(room_id)
    room.phase = GamePhase.CARD_PLAY
    # Alice 不出 G7，直接合技
    rm.get_room(room_id).turn_player_id = bob
    client.post("/api/card/use", json={"room_id": room_id, "card_id": "G1_xuxiake", "player_id": bob})
    rm.get_room(room_id).turn_player_id = alice
    r = client.post("/api/card/combo", json={"room_id": room_id, "cards": ["G7_lishizhen", "G1_xuxiake"], "player_id": alice})
    assert r.status_code == 400
    assert "G7李时珍" in r.json().get("detail", "")


# ============ P1 #10：重连 ============
def test_rejoin_recovers_player_in_known_room(client, rm):
    """已知 room_id + player_id → 重连成功。"""
    r = client.post("/api/room/create", json={"user_name": "Alice"})
    room_id = r.json()["room_id"]
    pid = r.json()["player_id"]
    r = client.post("/api/room/rejoin", json={"room_id": room_id, "player_id": pid})
    assert r.status_code == 200
    assert r.json()["player_id"] == pid


def test_rejoin_unknown_player_404(client, rm):
    """player_id 不属于房间 → 404。"""
    r = client.post("/api/room/create", json={"user_name": "Alice"})
    room_id = r.json()["room_id"]
    r = client.post("/api/room/rejoin", json={"room_id": room_id, "player_id": "fake"})
    assert r.status_code == 404


def test_ttl_expires_room(rm):
    """手动调 TTL 短一点，验证 gc_expired 把它清掉。"""
    short_rm = RoomManagerShortTTL(ttl_seconds=1)
    r = short_rm.create_room("Alice")
    rid = r.room_id
    assert short_rm.get_room(rid) is r
    time.sleep(1.2)
    expired = short_rm.gc_expired()
    assert rid in expired
    assert short_rm.get_room(rid) is None


# ============ P2 #14: state 合并数据 ============
def test_state_endpoint_include_static(client):
    """include_static=true 时同时返回 cards/questions/knowledge。"""
    r = client.post("/api/room/create", json={"user_name": "Alice"})
    room_id = r.json()["room_id"]
    r = client.get(f"/api/room/state/{room_id}?include_static=true")
    assert r.status_code == 200
    body = r.json()
    assert "room" in body
    assert "cards" in body
    assert "questions" in body
    assert "knowledge" in body
    assert isinstance(body["cards"], list)


def test_state_endpoint_default_no_static(client):
    """默认不带静态数据。"""
    r = client.post("/api/room/create", json={"user_name": "Alice"})
    room_id = r.json()["room_id"]
    r = client.get(f"/api/room/state/{room_id}")
    assert r.status_code == 200
    body = r.json()
    assert "room" in body
    assert "cards" not in body


# ============ P1 #12：clues_log 返回 content ============
def test_state_returns_clue_content(client, rm):
    """出了卡后，state 里能看到线索 content。"""
    from game.state import GamePhase
    r = client.post("/api/room/create", json={"user_name": "Alice"})
    room_id = r.json()["room_id"]
    pid = r.json()["player_id"]
    rm.get_room(room_id).phase = GamePhase.QUESTIONING
    client.post("/api/card/use", json={"room_id": room_id, "card_id": "G1_xuxiake", "player_id": pid})
    r = client.get(f"/api/room/state/{room_id}")
    body = r.json()
    clue = body["room"]["clues_log"][0]
    assert "content" in clue
    assert clue["content"]  # 非空


# ============ Dev-only ============
def test_dev_reload_data(client):
    r = client.post("/api/dev/reload_data")
    assert r.status_code == 200
    assert "script" in r.json()["reloaded"]


def test_dev_gc_rooms(client):
    r = client.post("/api/dev/gc_rooms")
    assert r.status_code == 200
    assert "expired" in r.json()


# ============ 帮助：短 TTL RoomManager ============
class RoomManagerShortTTL:
    """手动构造一个 Room 字典 + 短 TTL 验证 gc_expired，不启动真线程。"""
    def __init__(self, ttl_seconds: int):
        from game.state import RoomManager
        self._inner = RoomManager(ttl_seconds=ttl_seconds)
        self._inner._gc_stop.set()  # 关掉后台线程，单测里手控 gc
        if self._inner._gc_thread:
            self._inner._gc_thread.join(timeout=0.1)

    def create_room(self, user_name):
        return self._inner.create_room(user_name)

    def get_room(self, rid):
        return self._inner.get_room(rid)

    def gc_expired(self):
        return self._inner.gc_expired()

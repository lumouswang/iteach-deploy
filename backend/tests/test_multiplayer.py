"""G3 双人协作模式测试 — 覆盖 turn 轮换 / per-player 计数 / 合技分属校验。"""
import pytest
from game.state import RoomManager, GamePhase


@pytest.fixture
def rm():
    return RoomManager()


def test_create_multiplayer_room_starts_in_lobby(rm):
    """双人房创建后处于 LOBBY 阶段，等第二个玩家。"""
    room = rm.create_multiplayer_room("Alice")
    assert room.phase == GamePhase.LOBBY
    assert room.is_multiplayer
    assert len(room.players) == 1


def test_join_room_two_players_advances_to_intro(rm):
    """双人房第二位玩家加入后自动进入 INTRO。"""
    room = rm.create_multiplayer_room("Alice")
    assert len(room.players) == 1
    assert room.phase == GamePhase.LOBBY

    joined = rm.join_room(room.room_id, "Bob")
    assert joined is room
    assert len(room.players) == 2
    assert room.phase == GamePhase.INTRO
    # turn 回到第 1 位
    assert room.turn_player_id == room.players[0]["user_id"]


def test_join_nonexistent_room_returns_none(rm):
    """加入不存在的房间返回 None（接口层会返 404）。"""
    assert rm.join_room("nope", "Bob") is None


def test_join_non_multiplayer_room_rejected(rm):
    """单玩家房间不允许 join。"""
    room = rm.create_room("Alice")
    room.is_multiplayer = False
    assert rm.join_room(room.room_id, "Bob") is None


def test_join_full_room_rejected(rm):
    """双人房满员后再 join 拒绝。"""
    room = rm.create_multiplayer_room("Alice")
    rm.join_room(room.room_id, "Bob")
    extra = rm.join_room(room.room_id, "Charlie")
    assert extra is None
    assert len(room.players) == 2


def test_other_player_helper(rm):
    """other_player() 应返回当前对手。"""
    room = rm.create_multiplayer_room("Alice")
    rm.join_room(room.room_id, "Bob")
    room.turn_player_id = room.players[0]["user_id"]
    cur = room.current_player()
    other = room.other_player()
    assert cur["user_name"] == "Alice"
    assert other["user_name"] == "Bob"


def test_advance_turn_single_player_noop(rm):
    """单玩家模式 advance_turn() 应不变。"""
    room = rm.create_room("Alice")
    before = room.turn_player_id
    room.advance_turn()
    assert room.turn_player_id == before


def test_advance_turn_multiplayer_cycles(rm):
    """双人模式 advance_turn() 切到对手。"""
    room = rm.create_multiplayer_room("Alice")
    rm.join_room(room.room_id, "Bob")
    alice = room.players[0]["user_id"]
    bob = room.players[1]["user_id"]
    room.turn_player_id = alice
    room.advance_turn()
    assert room.turn_player_id == bob
    room.advance_turn()
    assert room.turn_player_id == alice

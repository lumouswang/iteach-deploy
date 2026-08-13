"""G3 引擎层双人回合校验测试。"""
import pytest
from main import (
    room_manager, game_engine, question_judge, deck_engine
)


@pytest.fixture
def mp_room():
    """双人协作房间（2 人已到齐，phase=INTRO）"""
    room = room_manager.create_multiplayer_room("Alice")
    joined = room_manager.join_room(room.room_id, "Bob")
    game_engine.start_multiplayer(room)
    return room


def test_ask_question_turn_check_blocks_other_player(mp_room):
    """非 turn 玩家的提问被拒。"""
    alice = mp_room.players[0]["user_id"]
    bob = mp_room.players[1]["user_id"]
    mp_room.turn_player_id = alice

    r = game_engine.ask_question(mp_room, "Q01", question_judge, player_id=bob)
    assert r["ok"] is False
    assert "不是" in r["error"] or "轮到你" in r["error"]


def test_ask_question_advance_turn_after_action(mp_room):
    """提问成功后自动切轮到对手。"""
    alice = mp_room.players[0]["user_id"]
    bob = mp_room.players[1]["user_id"]
    mp_room.phase = __import__("game.state", fromlist=["GamePhase"]).GamePhase.QUESTIONING
    mp_room.turn_player_id = alice
    r = game_engine.ask_question(mp_room, "Q01", question_judge, player_id=alice)
    assert r["ok"] is True
    assert r["turn_player_id"] == bob
    assert mp_room.turn_player_id == bob


def test_per_player_question_budget(mp_room):
    """双人模式下每位玩家有独立 5 次提问预算。"""
    mp_room.phase = __import__("game.state", fromlist=["GamePhase"]).GamePhase.QUESTIONING
    alice = mp_room.players[0]["user_id"]
    mp_room.turn_player_id = alice

    r = game_engine.ask_question(mp_room, "Q01", question_judge, player_id=alice)
    assert r["ok"]
    assert r["questions_remaining"] == 4

    # alice 跑完 4 次后第 5 次被拒
    mp_room.questions_per_player[alice] = 1
    mp_room.turn_player_id = alice
    r = game_engine.ask_question(mp_room, "Q02", question_judge, player_id=alice)
    assert r["ok"]
    mp_room.turn_player_id = alice
    r = game_engine.ask_question(mp_room, "Q03", question_judge, player_id=alice)
    assert r["ok"] is False


def test_play_card_records_owner(mp_room):
    """出卡应记录 player_id。"""
    alice = mp_room.players[0]["user_id"]
    mp_room.phase = __import__("game.state", fromlist=["GamePhase"]).GamePhase.CARD_PLAY
    mp_room.turn_player_id = alice
    r = game_engine.play_single_card(mp_room, "G1_xuxiake", deck_engine, player_id=alice)
    assert r["ok"]
    assert mp_room.clues_log[-1].player_id == alice
    assert mp_room.per_player_card_usage[alice]["G1_xuxiake"] == 1


def test_combo_requires_two_different_owners_in_mp(mp_room):
    """双人模式合技要求 2 张卡分属不同玩家。"""
    alice = mp_room.players[0]["user_id"]
    bob = mp_room.players[1]["user_id"]
    mp_room.phase = __import__("game.state", fromlist=["GamePhase"]).GamePhase.CARD_PLAY
    mp_room.turn_player_id = alice

    # 让 Alice 同时拥有 G1+G2（不合规）
    r = game_engine.play_single_card(mp_room, "G1_xuxiake", deck_engine, player_id=alice)
    mp_room.turn_player_id = alice
    r = game_engine.play_single_card(mp_room, "G2_shenkuo", deck_engine, player_id=alice)
    mp_room.turn_player_id = alice
    # 合技：G1+G2 但都属 alice
    r = game_engine.try_unlock_layer(mp_room, ["G1_xuxiake", "G2_shenkuo"], deck_engine, player_id=alice)
    assert r["ok"] is False
    assert "两人" in r["error"] or "分属" in r["error"] or "双人模式" in r["error"]


def test_single_player_mode_unaffected():
    """向后兼容：单玩家模式不需要 player_id。"""
    room = room_manager.create_room("solo")
    from game.state import GamePhase
    room.phase = GamePhase.CARD_PLAY
    r = game_engine.play_single_card(room, "G1_xuxiake", deck_engine)
    # 没传 player_id，单玩家应 OK
    assert r["ok"]
    # 用单人 age 表达 player_id=""（data 字段为空字符串）
    assert r.get("turn_player_id") is None or r.get("turn_player_id") == room.turn_player_id

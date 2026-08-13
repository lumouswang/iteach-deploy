"""P0 #5：G7 链结合技要求 G7 自己已用过一次。"""
import pytest
from main import (
    room_manager, game_engine, deck_engine
)
from game.state import GamePhase


@pytest.fixture
def mp_room():
    room = room_manager.create_multiplayer_room("Alice")
    room_manager.join_room(room.room_id, "Bob")
    game_engine.start_multiplayer(room)
    room.phase = GamePhase.CARD_PLAY
    return room


def test_g7_combo_requires_g7_used_enforced_in_mp(mp_room):
    """双人 G7 链结合技：G7 必须由 owner 自己先用过一次。"""
    alice = mp_room.players[0]["user_id"]
    bob = mp_room.players[1]["user_id"]
    # 现象层/条件层/微观层全部解锁（让 ultimate 层锁通过）
    mp_room.unlocked_layers = ["phenomenon", "condition", "microscopic"]

    # Bob 出 G1（这张会被当作 G7 链结合技的"另一张"）
    mp_room.turn_player_id = bob
    game_engine.play_single_card(mp_room, "G1_xuxiake", deck_engine, player_id=bob)
    # Alice 不出 G7，直接合技
    mp_room.turn_player_id = alice
    r = game_engine.try_unlock_layer(mp_room, ["G7_lishizhen", "G1_xuxiake"], deck_engine, player_id=alice)
    assert r["ok"] is False
    assert "G7李时珍" in r["error"]


def test_g7_combo_g7_used_then_succeeds(mp_room):
    """G7 自己用过一次后 → 链结合技允许。"""
    alice = mp_room.players[0]["user_id"]
    bob = mp_room.players[1]["user_id"]
    mp_room.unlocked_layers = ["phenomenon", "condition", "microscopic"]

    # Alice 自己出 G7 一次（拿到 1 条线索）
    mp_room.turn_player_id = alice
    game_engine.play_single_card(mp_room, "G7_lishizhen", deck_engine, player_id=alice)
    # Bob 出 G1
    mp_room.turn_player_id = bob
    game_engine.play_single_card(mp_room, "G1_xuxiake", deck_engine, player_id=bob)
    # Alice 合技
    mp_room.turn_player_id = alice
    r = game_engine.try_unlock_layer(mp_room, ["G7_lishizhen", "G1_xuxiake"], deck_engine, player_id=alice)
    assert r["ok"] is True
    assert r["unlock_layer"] == "ultimate"


def test_g7_combo_other_card_not_used_blocked(mp_room):
    """链结合技：另一张卡必须也用过。"""
    alice = mp_room.players[0]["user_id"]
    bob = mp_room.players[1]["user_id"]
    mp_room.unlocked_layers = ["phenomenon", "condition", "microscopic"]

    # Alice 出 G7（满足 G7 自己已用）
    mp_room.turn_player_id = alice
    game_engine.play_single_card(mp_room, "G7_lishizhen", deck_engine, player_id=alice)
    # Bob 不出 G1，直接合技
    mp_room.turn_player_id = alice
    r = game_engine.try_unlock_layer(mp_room, ["G7_lishizhen", "G1_xuxiake"], deck_engine, player_id=alice)
    assert r["ok"] is False
    assert "G1_xuxiake" in r["error"] or "必须先出过" in r["error"]

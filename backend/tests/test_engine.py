"""游戏引擎核心规则测试 — 12 用例覆盖 B1/B2 修复回归 + 状态机关键分支。"""
import pytest
from game.state import GamePhase


# ============ 提问阶段 ============

def test_ask_in_intro_auto_advances_to_questioning(engine, fresh_room, judge):
    """开局前置阶段提问一次后自动 → QUESTIONING（不是 CARD_PLAY）"""
    fresh_room.phase = GamePhase.INTRO
    r = engine.ask_question(fresh_room, "Q01", judge)
    assert r["ok"] is True
    assert fresh_room.phase == GamePhase.QUESTIONING
    assert fresh_room.questions_remaining == 4


def test_ask_5_times_advances_to_card_play(engine, fresh_room, judge):
    """5 次提问耗尽自动 → CARD_PLAY"""
    fresh_room.phase = GamePhase.QUESTIONING
    for i, qid in enumerate(["Q01", "Q02", "Q03", "Q04", "Q05"]):
        r = engine.ask_question(fresh_room, qid, judge)
        assert r["ok"], f"ask #{i+1} failed: {r}"
    assert fresh_room.questions_remaining == 0
    assert fresh_room.phase == GamePhase.CARD_PLAY


def test_ask_6th_blocked(engine, fresh_room, judge):
    """6 次提问被拒绝"""
    fresh_room.phase = GamePhase.QUESTIONING
    fresh_room.questions_remaining = 0
    r = engine.ask_question(fresh_room, "Q01", judge)
    assert r["ok"] is False
    assert "提问次数" in r["error"]


def test_ask_negation_goes_to_negation_board(engine, fresh_room, judge):
    """点"否"的提问自动进入否决板"""
    fresh_room.phase = GamePhase.QUESTIONING
    # Q02 answer is "否" (radiation cooling)
    r = engine.ask_question(fresh_room, "Q02", judge)
    assert r["ok"]
    assert r["qa"]["is_negation"] is True
    assert len(fresh_room.negation_board) == 1
    assert fresh_room.negation_board[0].qid == "Q02"


# ============ 出卡阶段 (B2 修复) ============

def test_play_card_in_intro_blocked(engine, fresh_room, deck):
    """B2 修复回归：INTRO 阶段禁出卡，返回 4xx 风格错误"""
    fresh_room.phase = GamePhase.INTRO
    r = engine.play_single_card(fresh_room, "G1_xuxiake", deck)
    assert r["ok"] is False
    assert "开局前置" in r["error"]


def test_play_card_records_clue_and_increments_usage(engine, fresh_room, deck):
    """单卡出牌：clues_log +1, card_usage +1"""
    fresh_room.phase = GamePhase.CARD_PLAY
    r = engine.play_single_card(fresh_room, "G1_xuxiake", deck)
    assert r["ok"], r
    assert len(fresh_room.clues_log) == 1
    assert fresh_room.card_usage["G1_xuxiake"] == 1


def test_play_card_max_use_limit(engine, fresh_room, deck):
    """卡 max_use 上限阻止继续出"""
    fresh_room.phase = GamePhase.CARD_PLAY
    # G1_xuxiake 默认 max_use=2，跑两次 ok
    for _ in range(2):
        r = engine.play_single_card(fresh_room, "G1_xuxiake", deck)
        assert r["ok"], r
    # 第 3 次被拒
    r = engine.play_single_card(fresh_room, "G1_xuxiake", deck)
    assert r["ok"] is False
    assert "上限" in r["error"]


# ============ 合技 + 层锁 ============

def test_unlock_phenomenon_layer_happy_path(engine, fresh_room, deck):
    """徐霞客 + 沈括 → 解锁现象层"""
    fresh_room.phase = GamePhase.CARD_PLAY
    r = engine.try_unlock_layer(fresh_room, ["G1_xuxiake", "G2_shenkuo"], deck)
    assert r["ok"], r
    assert r["unlock_layer"] == "phenomenon"
    assert "phenomenon" in fresh_room.unlocked_layers


def test_unlock_microscopic_without_condition_blocked(engine, fresh_room, deck):
    """跳过现象/条件层直接打微观层 → 被层锁拒绝"""
    fresh_room.phase = GamePhase.CARD_PLAY
    # 不解锁 phenomenon/condition 直接解锁 microscopic（宋应星+徐光启 → microscopic）
    r = engine.try_unlock_layer(fresh_room, ["G3_songyingxing", "G4_xuguangqi"], deck)
    assert r["ok"] is False
    assert "现象层" in r["error"] or "线索不足" in r["error"]


def test_wrong_combo_blocked(engine, fresh_room, deck):
    """两张不能配对的卡不能合技"""
    fresh_room.phase = GamePhase.CARD_PLAY
    r = engine.try_unlock_layer(fresh_room, ["G1_xuxiake", "G7_lishizhen"], deck)
    assert r["ok"] is False


# ============ B1 修复回归 ============

def test_clue_attribution_only_fills_combo_cards(engine, fresh_room, deck):
    """B1 修复回归：
    解锁层时只回填本次合技参与卡的最新一条线索，
    而不是把全部未归层线索一刀切打到当前层。
    """
    fresh_room.phase = GamePhase.CARD_PLAY

    # 先单卡出两张碎片（不参与合技）— 这些线索应该保持 layer=None
    engine.play_single_card(fresh_room, "G5_zouchongzhi", deck)  # 它不在 G1+G2 combo 里
    engine.play_single_card(fresh_room, "G6_mozi", deck)          # 它也不在
    assert all(c.layer is None for c in fresh_room.clues_log)

    # 再出 G1 (combo 参与卡，但不参与合一)
    engine.play_single_card(fresh_room, "G1_xuxiake", deck)
    assert fresh_room.clues_log[-1].layer is None  # 还没合技 → 仍 None

    # 触发合技：G1+G2 → 解锁 phenomenon
    r = engine.try_unlock_layer(fresh_room, ["G1_xuxiake", "G2_shenkuo"], deck)
    assert r["ok"], r

    # 检验：G1 的最新一条线索应被归到 phenomenon，其他保持 None
    g1_clues = [c for c in fresh_room.clues_log if c.card_id == "G1_xuxiake"]
    g2_clues = [c for c in fresh_room.clues_log if c.card_id == "G2_shenkuo"]
    g5_clues = [c for c in fresh_room.clues_log if c.card_id == "G5_zouchongzhi"]
    g6_clues = [c for c in fresh_room.clues_log if c.card_id == "G6_mozi"]

    assert g1_clues[-1].layer == "phenomenon", "G1 最后一条应被归 phenomenon"
    # 其他非 combo 卡应不受影响
    for c in g5_clues + g6_clues:
        assert c.layer is None, f"{c.card_id} 的线索不应被一刀切归层"


# ============ reveal / debrief 死代码接通 (B5 顺手测) ============

def test_reveal_requires_ultimate(engine, fresh_room):
    """未解锁终极层时不能揭晓"""
    fresh_room.phase = GamePhase.CARD_PLAY
    r = engine.reveal_ultimate(fresh_room)
    assert r["ok"] is False
    assert "终极层" in r["error"]


def test_reveal_returns_all_unlocked_layers(engine, fresh_room):
    """B5 修复：揭晓返已解锁层的全部 reveal_text + room state"""
    fresh_room.unlocked_layers = ["phenomenon", "condition", "microscopic", "ultimate"]
    r = engine.reveal_ultimate(fresh_room)
    assert r["ok"]
    assert fresh_room.phase == GamePhase.REVEAL
    assert "phenomenon" in r["layers"]
    assert "ultimate" in r["layers"]
    assert r["layers"]["ultimate"].get("reveal_text")


def test_to_debrief_advances_phase(engine, fresh_room):
    """to_debrief 推进 phase=DEBRIEF"""
    fresh_room.phase = GamePhase.REVEAL
    r = engine.to_debrief(fresh_room)
    assert r["ok"]
    assert fresh_room.phase == GamePhase.DEBRIEF


def test_to_extend_advances_phase(engine, fresh_room):
    """to_extend 推进 phase=EXTEND"""
    fresh_room.phase = GamePhase.DEBRIEF
    r = engine.to_extend(fresh_room)
    assert r["ok"]
    assert fresh_room.phase == GamePhase.EXTEND


def test_reveal_http_endpoint(client):
    """B5 路由 /api/room/reveal 贯通"""
    r = client.post("/api/room/create", json={"user_name": "t"})
    room_id = r.json()["room_id"]
    # 手动加 ultimate（模拟以解锁终极层）
    from main import room_manager
    room = room_manager.get_room(room_id)
    room.unlocked_layers.append("ultimate")
    r = client.post("/api/room/reveal", json={"room_id": room_id})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "ultimate" in body["layers"]
    assert room.phase.value == "reveal"


def test_debrief_http_endpoint(client):
    """B5 路由 /api/room/debrief 贯通"""
    r = client.post("/api/room/create", json={"user_name": "t"})
    room_id = r.json()["room_id"]
    r = client.post("/api/room/debrief", json={"room_id": room_id})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    from main import room_manager
    assert room_manager.get_room(room_id).phase.value == "debrief"


# ============ 防剧透接口 ============

def test_cards_endpoint_default_hides_content(client):
    """U1 修复：默认 GET /api/cards 不暴露 clues[].content"""
    r = client.get("/api/cards")
    assert r.status_code == 200
    data = r.json()
    for card in data["cards"]:
        for clue in card["clues"]:
            assert "content" not in clue, f"card {card['id']} clue {clue.get('id')} leak content"


def test_cards_endpoint_reveal_true_returns_full(client):
    """reveal=true 时（含教师/调试视图）才返回 content"""
    r = client.get("/api/cards?reveal=true")
    assert r.status_code == 200
    cards = r.json()["cards"]
    # 至少一张卡有 content（数据完整性验证）
    has_content = any(
        any("content" in cl for cl in c["clues"])
        for c in cards
    )
    assert has_content


def test_card_clue_endpoint_requires_room_use(client):
    """U1 修复：未实际出卡 (card_usage[idx]=0) 时 GET clue 被 403"""
    # 先建一个房间
    r = client.post("/api/room/create", json={"user_name": "tester"})
    room_id = r.json()["room_id"]
    # 不出卡直接查 G1 的 idx=0 线索
    r = client.get(f"/api/card/clue?room_id={room_id}&card_id=G1_xuxiake&idx=0")
    assert r.status_code == 403

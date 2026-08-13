"""汤探局 - 游戏规则引擎（衔接状态机和卡牌/提问）"""
import logging
from time import time
from typing import Dict, Any, Optional, List

from .state import Room, GamePhase, QARecord, ClueRecord
from .questions import QuestionJudge
from .deck import DeckEngine

logger = logging.getLogger("tangtanju.engine")


class GameEngine:
    """中央调度：处理玩家动作、更新状态、产生广播事件"""

    def __init__(self, script_data: Dict[str, Any], cards_data: Dict[str, Any]):
        self._script = script_data
        self._cards = cards_data

    @property
    def script(self) -> Dict[str, Any]:
        return self._script

    @property
    def cards(self) -> Dict[str, Any]:
        return self._cards

    # ============ 工具 ============

    def _verify_turn(self, room: Room, player_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """G3 修复：双人模式下，只有 turn_player 才可行动。"""
        if not room.is_multiplayer:
            return None
        me_id = player_id or ""
        if not me_id:
            return {"ok": False, "error": "双人模式需要传入 player_id"}
        if room.turn_player_id != me_id:
            cur = room.current_player()
            return {
                "ok": False,
                "error": f"还没轮到你（现在是 {cur['user_name'] if cur else '?'} 的回合）"
            }
        return None

    def _finish_action(self, room: Room) -> None:
        """G3：双人模式动作完成后自动切轮到对手。"""
        if room.is_multiplayer:
            room.advance_turn()

    # ============ 状态机驱动 ============

    def start_game(self, room: Room) -> None:
        room.phase = GamePhase.INTRO

    def start_multiplayer(self, room: Room) -> None:
        """G3：LOBBY → INTRO，turn 切到 player 0。"""
        room.phase = GamePhase.INTRO
        if room.players:
            room.turn_player_id = room.players[0]["user_id"]

    # ============ 玩家动作 ============

    def ask_question(self, room: Room, qid: str, judge: QuestionJudge,
                     player_id: Optional[str] = None) -> Dict[str, Any]:
        """玩家提问。双人模式下 player_id 必须等于 turn_player_id。"""
        if room.phase != GamePhase.QUESTIONING:
            return {"ok": False, "error": "当前不在提问阶段"}
        turn_err = self._verify_turn(room, player_id)
        if turn_err:
            return turn_err

        if room.is_multiplayer:
            me = player_id or (room.players[0]["user_id"] if room.players else "")
            if room.questions_per_player.get(me, 0) <= 0:
                return {"ok": False, "error": "你的提问次数已用尽，轮到对手"}
            room.questions_per_player[me] = room.questions_per_player.get(me, 0) - 1
            remaining = room.questions_per_player[me]
        else:
            if room.questions_remaining <= 0:
                return {"ok": False, "error": "提问次数已用尽，请使用武将卡推进推理"}
            room.questions_remaining -= 1
            remaining = room.questions_remaining

        result = judge.judge(qid)
        if not result:
            return {"ok": False, "error": "无效的提问编号"}

        rec = QARecord(
            qid=result["qid"],
            category=result["category"],
            text=result["text"],
            answer=result["answer"],
            hint=result["hint"],
            knowledge_point=result["knowledge_point"],
            timestamp=time(),
            player_id=player_id or (room.players[0]["user_id"] if room.players else ""),
        )
        room.questions_log.append(rec)
        if judge.is_negation(result["answer"]):
            room.negation_board.append(rec)

        # 提问次数耗尽：自动切换到出卡阶段
        next_phase_hint = None
        if not room.is_multiplayer:
            if room.questions_remaining == 0:
                room.phase = GamePhase.CARD_PLAY
                next_phase_hint = "提问次数耗尽，自动进入出卡阶段"
        else:
            # 双人：仅当所有人都用完提问次数才进 CARD_PLAY
            if all(v <= 0 for v in room.questions_per_player.values()):
                room.phase = GamePhase.CARD_PLAY
                next_phase_hint = "全部玩家提问次数耗尽，自动进入出卡阶段"

        self._finish_action(room)
        logger.info("ask room=%s player=%s qid=%s answer=%s",
                    room.room_id, rec.player_id, rec.qid, rec.answer)

        return {
            "ok": True,
            "qa": {
                "qid": rec.qid,
                "category": rec.category,
                "text": rec.text,
                "answer": rec.answer,
                "hint": rec.hint,
                "knowledge_point": rec.knowledge_point,
                "is_negation": judge.is_negation(result["answer"]),
                "suggested_card": result.get("suggested_card", ""),
                "player_id": rec.player_id,
            },
            "questions_remaining": remaining,
            "turn_player_id": room.turn_player_id,
            "next_phase_hint": next_phase_hint,
        }

    # ============ 内部：卡牌使用计数（P1 #8 唯一真源） ============
    def _count_used(self, room: Room, card_id: str, player_id: str) -> int:
        """per_player 为唯一真源；单人模式自动归到 player 0"""
        if room.is_multiplayer:
            return room.per_player_card_usage.get(player_id, {}).get(card_id, 0)
        # 单人：归到第一个玩家
        me = player_id or (room.players[0]["user_id"] if room.players else "")
        return room.per_player_card_usage.get(me, {}).get(card_id, 0)

    def _increment_used(self, room: Room, card_id: str, player_id: str) -> None:
        if room.is_multiplayer:
            ppc = room.per_player_card_usage.setdefault(player_id, {})
            ppc[card_id] = ppc.get(card_id, 0) + 1
        else:
            me = player_id or (room.players[0]["user_id"] if room.players else "")
            ppc = room.per_player_card_usage.setdefault(me, {})
            ppc[card_id] = ppc.get(card_id, 0) + 1
        # 写回全局 card_usage（为了向后兼容报告/旧前端）
        room.card_usage[card_id] = room.card_usage.get(card_id, 0) + 1

    def play_single_card(
        self, room: Room, card_id: str, deck: DeckEngine,
        player_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """阶段3：单武将出牌（拿碎片线索）"""
        turn_err = self._verify_turn(room, player_id)
        if turn_err:
            return turn_err
        if room.phase == GamePhase.INTRO:
            return {"ok": False, "error": "开局前置阶段，请先完成至少1次提问"}
        if room.phase not in (GamePhase.CARD_PLAY, GamePhase.QUESTIONING):
            return {"ok": False, "error": "当前不在出卡阶段"}

        me = player_id or (room.players[0]["user_id"] if room.players else "")
        used = self._count_used(room, card_id, me)
        ok, msg = deck.can_use_card(card_id, used)
        if not ok:
            return {"ok": False, "error": msg}
        clue = deck.get_clue_at_index(card_id, used)
        if not clue:
            return {"ok": False, "error": "该卡已无更多线索"}
        self._increment_used(room, card_id, me)

        room.clues_log.append(ClueRecord(
            clue_id=clue["id"],
            card_id=card_id,
            label=clue["label"],
            content=clue["content"],
            knowledge_point=clue["knowledge_point"],
            player_id=me,
        ))

        if room.phase == GamePhase.QUESTIONING:
            room.phase = GamePhase.CARD_PLAY

        self._finish_action(room)
        logger.info("play_card room=%s player=%s card=%s used=%d",
                    room.room_id, me, card_id, used + 1)

        return {
            "ok": True,
            "card_id": card_id,
            "clue": clue,
            "card_usage": dict(room.card_usage),
            "per_player_card_usage": {k: dict(v) for k, v in room.per_player_card_usage.items()},
            "turn_player_id": room.turn_player_id,
        }

    def try_unlock_layer(
        self, room: Room, card_ids, deck: DeckEngine,
        player_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """G3 + 层锁：合技。双人模式要求 2 张卡分属不同玩家。"""
        if room.phase != GamePhase.CARD_PLAY:
            return {"ok": False, "error": "当前未进入出卡阶段"}
        turn_err = self._verify_turn(room, player_id)
        if turn_err:
            return turn_err

        me = player_id or (room.players[0]["user_id"] if room.players else "")

        # G3：双人模式特有校验 - 2 卡须分属不同玩家（除非复用对手已用过的卡）
        if room.is_multiplayer and len(room.players) >= 2:
            # 每人必须至少贡献 1 张卡（但允许一张卡同时被两人拥有 → 只要 distict owners >= 2）
            all_owners = {me}  # 合技发起者本身算一个 owner
            for cid in card_ids:
                for c in room.clues_log:
                    if c.card_id == cid:
                        all_owners.add(c.player_id)
            if len(all_owners) < 2:
                return {
                    "ok": False,
                    "error": "双人模式下，合技需要两人各出一张武将卡（请先用武将卡出牌）"
                }
            # 校验每张卡的 owner 的剩余使用次数
            for cid in card_ids:
                owner = me
                for c in reversed(room.clues_log):
                    if c.card_id == cid:
                        owner = c.player_id
                        break
                used = self._count_used(room, cid, owner)
                ok, msg = deck.can_use_card(cid, used)
                if not ok:
                    return {"ok": False, "error": msg}

        # G7 链结合技（P0 #5）：要求 G7 自己已用过一次
        # 从 script 读 ultimate 层的 G7 ID（不硬编码 G7_lishizhen）
        ultimate_cfg = self._script.get("layers", {}).get("ultimate", {})
        g7_id = None
        unlock_any = ultimate_cfg.get("unlock_cards_any", "")
        if isinstance(unlock_any, str):
            # 格式："G7_xxx + 任意已用1"
            head = unlock_any.split("+")[0].strip()
            if head.startswith("G"):
                g7_id = head.split()[0]  # 取首词
        if g7_id and g7_id in card_ids:
            other = [c for c in card_ids if c != g7_id]
            if len(other) != 1:
                return {"ok": False, "error": f"链结合技：必须 {g7_id} + 任意 1 张已用过的卡"}
            other_id = other[0]
            # G7 自己当前 owner 的使用次数必须 >= 1
            g7_owner = me
            for c in reversed(room.clues_log):
                if c.card_id == g7_id:
                    g7_owner = c.player_id
                    break
            g7_used = self._count_used(room, g7_id, g7_owner)
            if g7_used < 1:
                g7_card = self._cards.get("cards", []) and next((x for x in self._cards.get("cards", []) if x["id"] == g7_id), None)
                g7_name = g7_card["name"] if g7_card else g7_id
                return {"ok": False, "error": f"链结合技：{g7_name}必须先出过 1 次线索"}
            # 另一张卡也得被用过（来自 clues_log）
            other_used = any(c.card_id == other_id for c in room.clues_log)
            if not other_used:
                return {"ok": False, "error": f"链结合技：{other_id} 必须先出过 1 次线索"}

        # 不校验卡牌使用上限：合技是元数据动作，不需要额外“使用”次数。
        # （双人手模式下，上面的 owner-级 use 检查已保证两人各出过 1 条线索；这里不需要再拦。）

        result = deck.try_combo(list(card_ids), room.unlocked_layers)
        if not result["ok"]:
            return result

        # 注意：合技不消耗卡牌使用次数！
        # max_use 2 是「出线索」的上限（2 张碎片/卡），合技是元数据动作，不应额外计数。
        # 旧逻辑会在合技后 _increment_used，导致已用尽的卡不能合技（「徐霞客要用三次」bug）。

        layer_key = result["unlock_layer"]
        if layer_key not in room.unlocked_layers:
            room.unlocked_layers.append(layer_key)

        room.combo_history.append({
            "combo": result["combo_name"],
            "cards": card_ids,
            "unlocked": layer_key,
            "by_player": me,
        })

        # 把本次合技解锁的「层揭示文本」也作为一条 ClueRecord 存进 clues_log
        # 这样复盘报告能看见玩家靠合技拿到的整层深度解释，而不仅是单卡出线索
        layer_cfg = result.get("layer_data", {})
        layer_name = layer_cfg.get("name", layer_key)
        combo_clue_id = f"combo_{layer_key}_{len(room.clues_log) + 1}"
        room.clues_log.append(ClueRecord(
            clue_id=combo_clue_id,
            card_id=f"+{card_ids[0]}+{card_ids[1] if len(card_ids) > 1 else ''}".strip('+'),
            label=f"⚡ {result.get('combo_name', '合技')} → {layer_name}",
            content=layer_cfg.get("reveal_text", ""),
            # 用 layer_key 当 knowledge_point（前端 /learn/:kpId 路由直接命中 learn_content.json 的 layers）
            # 注：bloom_level（"识记"/"理解"/...）只在 UI 上做布鲁姆标签展示，不应该成为深链 ID。
            knowledge_point=layer_key,
            layer=layer_key,
            player_id=me,
        ))

        # B1 修复：只回填本次合技参与卡的最新一条未归层线索
        for cid in card_ids:
            for cr in reversed(room.clues_log):
                if cr.card_id == cid and cr.layer is None:
                    cr.layer = layer_key
                    break

        self._finish_action(room)
        logger.info("combo room=%s player=%s cards=%s unlocked=%s",
                    room.room_id, me, card_ids, layer_key)

        return {
            "ok": True,
            "combo_name": result["combo_name"],
            "unlock_layer": layer_key,
            "layer_data": result["layer_data"],
            "unlocked_layers": room.unlocked_layers,
            "turn_player_id": room.turn_player_id,
        }

    def reveal_ultimate(self, room: Room) -> Dict[str, Any]:
        if "ultimate" not in room.unlocked_layers:
            return {"ok": False, "error": "请先解锁终极层"}
        room.phase = GamePhase.REVEAL
        layers_data: Dict[str, Any] = {}
        for k in ("phenomenon", "condition", "microscopic", "ultimate"):
            if k in room.unlocked_layers:
                layers_data[k] = self._script.get("layers", {}).get(k)
        return {
            "ok": True,
            "layers": layers_data,
            "unlocked_layers": room.unlocked_layers,
            "title": self._script.get("case_title", ""),
        }

    def to_debrief(self, room: Room) -> Dict[str, Any]:
        room.phase = GamePhase.DEBRIEF
        return {"ok": True}

    def to_extend(self, room: Room) -> Dict[str, Any]:
        room.phase = GamePhase.EXTEND
        return {"ok": True}

    def get_state(self, room: Room) -> Dict[str, Any]:
        return room.to_dict()

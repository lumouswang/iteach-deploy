"""汤探局 - 合技引擎 + 层锁校验"""
from typing import Dict, Any, List, Optional, Tuple


class DeckEngine:
    """处理武将卡出牌、合技组合、层锁校验"""

    def __init__(self, cards_data: Dict[str, Any], script_data: Dict[str, Any]):
        self._cards = {c["id"]: c for c in cards_data.get("cards", [])}
        self._combos = {c["layer"]: c for c in cards_data.get("combo_table", [])}
        self._layers = script_data.get("layers", {})

    def get_card(self, card_id: str) -> Optional[Dict[str, Any]]:
        return self._cards.get(card_id)

    def get_layer(self, layer_key: str) -> Optional[Dict[str, Any]]:
        return self._layers.get(layer_key)

    def list_cards(self) -> List[Dict[str, Any]]:
        return list(self._cards.values())

    def can_use_card(self, card_id: str, used_count: int) -> Tuple[bool, str]:
        """单卡 max_use 限制"""
        c = self.get_card(card_id)
        if not c:
            return False, "卡牌不存在"
        max_use = c.get("max_use", 2)
        if used_count >= max_use:
            return False, f"卡'{c['name']}'已达使用上限（{max_use}次）"
        return True, ""

    def get_clue_at_index(self, card_id: str, used_count: int) -> Optional[Dict[str, Any]]:
        """根据该卡已使用次数，返回下一条碎片线索"""
        c = self.get_card(card_id)
        if not c:
            return None
        clues = c.get("clues", [])
        if used_count < 0 or used_count >= len(clues):
            return None
        return clues[used_count]   # 第 0 次 -> 第 1 条；第 1 次 -> 第 2 条

    def try_combo(
        self,
        card_ids: List[str],
        unlocked_layers: List[str],
    ) -> Dict[str, Any]:
        """校验双人/链结合技
        返回: {ok, unlock_layer?, combo_name?, error?, layer_data?}

        设计变更（bug 调查）: 不再依赖 _combos/combo_table；
        从 script.layers[].unlock_cards 直接读，让数据为唯一真源。
        """
        if len(card_ids) != 2:
            return {"ok": False, "error": "必须选 2 张卡出合技"}

        # 从 script 的 layers 找精确配对
        for layer_key, layer_cfg in self._layers.items():
            unlock_cards = layer_cfg.get("unlock_cards", [])
            if isinstance(unlock_cards, list) and set(card_ids) == set(unlock_cards):
                prev_ok = self._check_prev_layer(layer_key, unlocked_layers)
                if not prev_ok:
                    needed = self._prev_layer_name(layer_key)
                    return {"ok": False, "error": f"线索不足，请先解开【{needed}】真相。"}
                return {
                    "ok": True,
                    "combo_name": layer_cfg.get("unlock_combo", "合技"),
                    "unlock_layer": layer_key,
                    "layer_data": layer_cfg,
                }

        # 链结合技（ultimate.unlock_cards_any: "G7_xuguangqi + 任意已用1"）
        ultimate = self._layers.get("ultimate", {})
        unlock_any = ultimate.get("unlock_cards_any", "")
        g7_id = None
        if isinstance(unlock_any, str) and "+" in unlock_any:
            head = unlock_any.split("+")[0].strip()
            if head.startswith("G"):
                g7_id = head.split()[0]
        if g7_id and g7_id in card_ids:
            prev_ok = self._check_prev_layer("ultimate", unlocked_layers)
            if not prev_ok:
                return {"ok": False, "error": "线索不足，请先解开【微观层】真相。"}
            return {
                "ok": True,
                "combo_name": ultimate.get("unlock_combo", "链结合技"),
                "unlock_layer": "ultimate",
                "layer_data": ultimate,
            }

        return {"ok": False, "error": "这两张卡不能配对合技（请选择正确的两位武将）"}

    def _check_prev_layer(self, target_layer: str, unlocked: List[str]) -> bool:
        LAYER_ORDER = ["phenomenon", "condition", "microscopic", "ultimate"]
        try:
            idx = LAYER_ORDER.index(target_layer)
        except ValueError:
            return False
        if idx == 0:
            return True
        prev = LAYER_ORDER[idx - 1]
        return prev in unlocked

    def _prev_layer_name(self, target_layer: str) -> str:
        LAYER_ORDER = ["phenomenon", "condition", "microscopic", "ultimate"]
        NAME_MAP = {
            "phenomenon": "现象层",
            "condition": "条件层",
            "microscopic": "微观层",
            "ultimate": "终极层",
        }
        try:
            idx = LAYER_ORDER.index(target_layer)
        except ValueError:
            return "上一层"
        if idx == 0:
            return "—"
        return NAME_MAP.get(LAYER_ORDER[idx - 1], "上一层")

"""
教师端 Dashboard 数据聚合模块 (P1)

提供：
- 班级进度总览
- 考点统计（14 个考点掌握率）
- 学情画像（每个学生的武将点亮情况）
- 答题热力图
- 课堂控制（暂停/恢复/广播/踢人）

设计原则：
- 不修改 Room/RoomManager 核心逻辑
- 在主路由里通过 dependency 注入
- 教师身份通过房间元数据识别（teacher_id 字段）
"""
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict

from game.state import RoomManager, Room

logger = logging.getLogger("tangtanju.teacher")

DATA_DIR = Path(__file__).parent.parent / "data"


class TeacherDashboard:
    """教师端数据聚合器"""

    def __init__(self, room_manager: RoomManager, script_data: Dict, cards_data: Dict):
        self._rooms = room_manager
        self._script = script_data
        self._cards = cards_data

        # 课堂控制：教师动作广播（暂停/恢复/踢人）
        self._control_state: Dict[str, Dict[str, Any]] = {}  # room_id -> {paused, broadcast_msg, kicked}

        # 答题统计（内存，重启清空；生产环境应该持久化）
        self._answer_stats: Dict[str, Dict] = defaultdict(lambda: {
            "total_questions": 0,
            "negation_count": 0,
            "combo_count": 0,
            "clue_count": 0,
            "layer_unlock_count": 0,
            "kp_hits": defaultdict(int),      # 考点命中次数
            "kp_miss": defaultdict(int),      # 考点失败次数
            "negation_patterns": [],           # 否决模式 [(layer, category)]
        })

        # 加载考点定义
        self._kp_definitions = self._load_kp_definitions()

    def _load_kp_definitions(self) -> List[Dict]:
        """从 knowledge_map.json 加载考点定义"""
        try:
            km = json.loads((DATA_DIR / "knowledge_map.json").read_text(encoding="utf-8"))
            kps = []
            for subj in km.get("subjects", []):
                for ep in subj.get("exam_points", []):
                    kps.append({
                        "subject": subj["name"],
                        "subject_icon": subj.get("icon", "📚"),
                        "subject_color": subj.get("color", "#909399"),
                        "name": ep["name"],
                        "weight": ep["weight"],
                        "trigger": ep.get("trigger", ""),
                    })
            return kps
        except Exception as e:
            logger.warning(f"加载考点定义失败: {e}")
            return []

    # ============================================================
    # 班级进度总览
    # ============================================================

    def get_class_overview(self, teacher_id: Optional[str] = None) -> Dict:
        """班级进度总览"""
        rooms = self._rooms.list_rooms()
        overview = {
            "teacher_id": teacher_id,
            "timestamp": datetime.now().isoformat(),
            "total_rooms": len(rooms),
            "active_rooms": 0,
            "total_students": 0,
            "rooms_detail": [],
            "aggregated": {
                "avg_layer_unlocked": 0.0,
                "avg_questions_used": 0.0,
                "avg_clues_collected": 0.0,
                "combo_success_rate": 0.0,
                "kp_mastery": {},  # {kp_name: {"hit": 0, "miss": 0, "mastery": 0.0-1.0}}
            },
        }

        total_layers = 0
        total_questions = 0
        total_clues = 0
        total_combos = 0
        total_combo_attempts = 0

        for room_info in rooms:
            room = self._rooms.get_room(room_info["room_id"])
            if not room:
                continue

            overview["active_rooms"] += 1
            overview["total_students"] += len(room.players)

            layers = len(room.unlocked_layers)
            questions = room.questions_used_total
            clues = len(room.clues_log)
            combos = len(room.combo_history)

            total_layers += layers
            total_questions += questions
            total_clues += clues
            total_combos += combos

            overview["rooms_detail"].append({
                "room_id": room.room_id,
                "case_id": room.case_id,
                "phase": room.phase.value if hasattr(room.phase, "value") else str(room.phase),
                "players": [{"user_id": p["user_id"], "user_name": p["user_name"]} for p in room.players],
                "is_multiplayer": room.is_multiplayer,
                "layers_unlocked": layers,
                "questions_used": questions,
                "clues_collected": clues,
                "combos_succeeded": combos,
                "control_state": self._control_state.get(room.room_id, {}),
                "created_at": getattr(room, "created_at", ""),
            })

        n = max(overview["active_rooms"], 1)
        overview["aggregated"]["avg_layer_unlocked"] = round(total_layers / n, 2)
        overview["aggregated"]["avg_questions_used"] = round(total_questions / n, 2)
        overview["aggregated"]["avg_clues_collected"] = round(total_clues / n, 2)
        overview["aggregated"]["combo_success_rate"] = round(
            (total_combos / max(total_combo_attempts, 1)) * 100, 1
        ) if total_combo_attempts else 0.0

        # 考点掌握率
        for kp in self._kp_definitions:
            kp_name = kp["name"]
            stats = self._answer_stats.get(kp_name, {"kp_hits": {}, "kp_miss": {}})
            hits = stats["kp_hits"].get(kp_name, 0)
            misses = stats["kp_miss"].get(kp_name, 0)
            total = hits + misses
            mastery = round((hits / total) * 100, 1) if total else 0.0
            overview["aggregated"]["kp_mastery"][kp_name] = {
                "hit": hits,
                "miss": misses,
                "mastery_pct": mastery,
                "subject": kp["subject"],
                "subject_color": kp["subject_color"],
                "weight": kp["weight"],
            }

        return overview

    # ============================================================
    # 学情画像（单个学生）
    # ============================================================

    def get_student_profile(self, room_id: str, user_id: str) -> Optional[Dict]:
        """单个学生的学情画像"""
        room = self._rooms.get_room(room_id)
        if not room:
            return None

        # 找这个学生在哪个房间
        player = next((p for p in room.players if p["user_id"] == user_id), None)
        if not player:
            return None

        # 该学生触发的线索 / 否决 / 合技
        my_clues = [c for c in room.clues_log if c.player_id == user_id]
        my_questions = [q for q in room.questions_log if getattr(q, "player_id", None) == user_id]
        my_negations = [q for q in room.negation_board if getattr(q, "player_id", None) == user_id]
        my_combos = [c for c in room.combo_history if getattr(c, "player_id", None) == user_id]

        # 已点亮武将（用过 / 合技过的卡）
        used_cards = set()
        for c in my_clues:
            if hasattr(c, "card_id"):
                used_cards.add(c.card_id)
        for cmb in my_combos:
            if hasattr(cmb, "card_ids"):
                used_cards.update(cmb.card_ids)

        # 思维风格判定
        style = self._infer_thinking_style(my_questions, my_combos)

        # 能力雷达图（5 维度）
        ability = self._calc_ability_score(my_clues, my_negations, my_combos, room)

        return {
            "room_id": room_id,
            "user_id": user_id,
            "user_name": player.get("user_name", ""),
            "stats": {
                "questions_asked": len(my_questions),
                "clues_found": len(my_clues),
                "negations": len(my_negations),
                "combos_succeeded": len([c for c in my_combos if getattr(c, "success", True)]),
                "cards_used": len(used_cards),
                "cards_total": len(self._cards.get("cards", [])),
                "layers_unlocked": [l for l in room.unlocked_layers],
            },
            "thinking_style": style,
            "ability_radar": ability,
            "kp_mastery": self._student_kp_mastery(my_clues),
            "negation_patterns": [
                {
                    "category": getattr(q, "category", ""),
                    "text": getattr(q, "text", "")[:60],
                    "layer": getattr(q, "layer", ""),
                }
                for q in my_negations[-10:]  # 最近 10 条
            ],
            "timeline": [
                {
                    "t": getattr(c, "timestamp", 0),
                    "type": "clue",
                    "card": getattr(c, "card_id", ""),
                    "kp": getattr(c, "knowledge_point", ""),
                }
                for c in my_clues
            ][-20:],
        }

    def _infer_thinking_style(self, questions, combos) -> str:
        """根据提问/合技推断思维风格"""
        if not questions:
            return "未参与"
        cats = [getattr(q, "category", "") for q in questions]
        cat_count = {c: cats.count(c) for c in set(cats)}
        dominant = max(cat_count, key=cat_count.get) if cat_count else "unknown"

        style_map = {
            "物质类": "📐 分析型（聚焦物质结构）",
            "环境变量类": "�️ 条件型（关注环境变化）",
            "力学系统类": "⚙️ 系统型（强调整体平衡）",
        }
        return style_map.get(dominant, f"混合型（{dominant}）")

    def _calc_ability_score(self, clues, negations, combos, room) -> Dict[str, float]:
        """计算 5 维能力雷达（0-100）"""
        # 观察力 = 线索数 / 期望线索
        clue_score = min(100, len(clues) * 12)

        # 判断力 = 1 - 否决率
        neg_rate = len(negations) / max(len(clues) + len(negations), 1)
        judge_score = max(0, 100 - neg_rate * 150)

        # 综合力 = 合技成功率
        combo_attempts = len(combos) if combos else 0
        combo_score = min(100, combo_attempts * 25)

        # 跨学科力 = 用过的卡覆盖的学科数
        subjects_used = set()
        for c in clues:
            kp = getattr(c, "knowledge_point", "")
            if "化学" in kp or "盐湖" in kp or "Ksp" in kp or "溶解" in kp:
                subjects_used.add("化学")
            if "毛细" in kp or "蒸发" in kp or "辐射" in kp or "物理" in kp:
                subjects_used.add("物理")
            if "化石" in kp or "嗜盐" in kp or "生物" in kp:
                subjects_used.add("生物")
            if "盐湖" in kp or "盆地" in kp or "水经" in kp or "地理" in kp:
                subjects_used.add("地理")
        cross_score = min(100, len(subjects_used) * 25)

        # 探究深度 = 解锁层数
        depth_score = min(100, len(room.unlocked_layers) * 25)

        return {
            "观察力": round(clue_score, 1),
            "判断力": round(judge_score, 1),
            "综合力": round(combo_score, 1),
            "跨学科力": round(cross_score, 1),
            "探究深度": round(depth_score, 1),
        }

    def _student_kp_mastery(self, clues) -> Dict[str, Dict]:
        """学生考点掌握情况"""
        kp_data = defaultdict(lambda: {"hit": 0, "miss": 0})
        for c in clues:
            kp = getattr(c, "knowledge_point", "")
            if not kp:
                continue
            # 简化：线索算 hit
            kp_data[kp]["hit"] += 1
        return {
            kp: {
                "hit": v["hit"],
                "miss": v["miss"],
                "mastery_pct": round((v["hit"] / max(v["hit"] + v["miss"], 1)) * 100, 1)
            }
            for kp, v in kp_data.items()
        }

    # ============================================================
    # 答题热力图
    # ============================================================

    def get_question_heatmap(self, room_id: str) -> Dict:
        """答题热力图数据（哪个学生卡在哪一题）"""
        room = self._rooms.get_room(room_id)
        if not room:
            return {"error": "room not found"}

        # 统计每个学生在每个层的提问 / 否决 / 合技次数
        heatmap = defaultdict(lambda: {
            "questions": 0,
            "negations": 0,
            "combos": 0,
            "clues": 0,
        })

        for q in room.questions_log:
            uid = getattr(q, "player_id", "unknown")
            heatmap[uid]["questions"] += 1

        for n in room.negation_board:
            uid = getattr(n, "player_id", "unknown")
            heatmap[uid]["negations"] += 1

        for c in room.clues_log:
            uid = getattr(c, "player_id", "unknown")
            heatmap[uid]["clues"] += 1

        for cmb in room.combo_history:
            uid = getattr(cmb, "player_id", "unknown")
            heatmap[uid]["combos"] += 1

        # 转成前端友好的数组格式（含 user_name）
        students_list = []
        for uid, stats in heatmap.items():
            player = next((p for p in room.players if p["user_id"] == uid), None)
            students_list.append({
                "user_id": uid,
                "user_name": player.get("user_name", "匿名") if player else "匿名",
                "questions": stats["questions"],
                "negations": stats["negations"],
                "combos": stats["combos"],
                "clues": stats["clues"],
            })

        # 找出"卡住的学生"（高否决 + 低合技）
        stuck_students = []
        for entry in students_list:
            if entry["negations"] >= 3 and entry["combos"] == 0:
                stuck_students.append({
                    "user_id": entry["user_id"],
                    "user_name": entry["user_name"],
                    "negations": entry["negations"],
                    "suggestion": "提问过多但未合技，建议教师引导组合"
                })

        return {
            "room_id": room_id,
            "students": students_list,
            "stuck_students": stuck_students,
            "total_negations": len(room.negation_board),
            "total_combos": len(room.combo_history),
        }

    # ============================================================
    # 课堂控制
    # ============================================================

    def pause_room(self, room_id: str, teacher_id: str) -> Dict:
        """暂停房间"""
        if room_id not in self._rooms._rooms:
            return {"ok": False, "error": "房间不存在"}
        self._control_state.setdefault(room_id, {})["paused"] = True
        self._control_state[room_id]["paused_by"] = teacher_id
        self._control_state[room_id]["paused_at"] = datetime.now().isoformat()
        return {"ok": True, "room_id": room_id, "paused": True}

    def resume_room(self, room_id: str, teacher_id: str) -> Dict:
        """恢复房间"""
        if room_id not in self._rooms._rooms:
            return {"ok": False, "error": "房间不存在"}
        self._control_state.setdefault(room_id, {})["paused"] = False
        return {"ok": True, "room_id": room_id, "paused": False}

    def broadcast_message(self, room_id: str, teacher_id: str, message: str) -> Dict:
        """向房间广播教师消息"""
        if room_id not in self._rooms._rooms:
            return {"ok": False, "error": "房间不存在"}
        self._control_state.setdefault(room_id, {})["broadcast_msg"] = {
            "text": message,
            "from": teacher_id,
            "at": datetime.now().isoformat(),
        }
        return {"ok": True, "room_id": room_id, "broadcast": message}

    def kick_student(self, room_id: str, teacher_id: str, user_id: str) -> Dict:
        """踢出学生"""
        room = self._rooms.get_room(room_id)
        if not room:
            return {"ok": False, "error": "房间不存在"}

        original_count = len(room.players)
        room.players = [p for p in room.players if p["user_id"] != user_id]
        if len(room.players) < original_count:
            self._control_state.setdefault(room_id, {})["kicked"] = user_id
            return {"ok": True, "kicked": user_id}
        return {"ok": False, "error": "学生不在房间"}

    def get_control_state(self, room_id: str) -> Dict:
        """获取课堂控制状态（学生端用来判断是否暂停）"""
        return self._control_state.get(room_id, {
            "paused": False,
            "broadcast_msg": None,
            "kicked": None,
        })

    # ============================================================
    # 答题统计上报（供后端 API 调用）
    # ============================================================

    def record_event(self, room_id: str, event_type: str, kp: Optional[str] = None,
                     layer: Optional[str] = None, category: Optional[str] = None,
                     success: bool = True) -> None:
        """上报答题事件（用于实时统计）"""
        if event_type == "negation" and kp:
            self._answer_stats[kp]["kp_miss"][kp] += 1
            self._answer_stats[kp]["negation_count"] += 1
            if category:
                self._answer_stats[kp]["negation_patterns"].append((layer, category))
        elif event_type == "clue" and kp:
            self._answer_stats[kp]["kp_hits"][kp] += 1
            self._answer_stats[kp]["clue_count"] += 1
        elif event_type == "combo":
            self._answer_stats["_global"]["combo_count"] += 1
            if not success:
                self._answer_stats["_global"]["negation_count"] += 1

    # ============================================================
    # 考点清单（教师参考用）
    # ============================================================

    def get_kp_catalog(self) -> List[Dict]:
        """返回所有考点 + 当前班级平均掌握率"""
        catalog = []
        for kp in self._kp_definitions:
            kp_name = kp["name"]
            stats = self._answer_stats.get(kp_name, {"kp_hits": {}, "kp_miss": {}})
            hits = sum(stats["kp_hits"].values())
            misses = sum(stats["kp_miss"].values())
            total = hits + misses
            mastery = round((hits / total) * 100, 1) if total else 0.0

            catalog.append({
                **kp,
                "class_mastery_pct": mastery,
                "class_hits": hits,
                "class_misses": misses,
                "status": "已掌握" if mastery >= 70 else "待加强" if mastery >= 40 else "未达标",
            })
        return catalog

    # ============================================================
    # 学生排行榜
    # ============================================================
    def get_leaderboard(self, sort_by: str = "total_score") -> Dict:
        """返回所有学生的综合排行榜。

        评分公式：
          total_score = clues*10 + combos*25 - negations*5 + layers*30
          其中 layers 数量额外加分（代表解锁深度）

        Args:
            sort_by: 排序键 (total_score / clues / combos / negations / layers)

        Returns:
            {
                "rankings": [
                    {
                        "rank": 1,
                        "user_id": "...",
                        "user_name": "...",
                        "room_id": "...",
                        "clues": 3,
                        "combos": 1,
                        "negations": 2,
                        "layers_unlocked": 2,
                        "questions_asked": 5,
                        "total_score": 95,
                        "badge": "🥇",  # 金/银/铜奖牌
                    },
                    ...
                ],
                "total_students": 6,
                "sort_by": "total_score"
            }
        """
        leaderboard: List[Dict] = []

        # 遍历所有房间收集学生
        for room_id in self._rooms.list_rooms():
            room = self._rooms.get_room(room_id)
            if not room:
                continue
            for player in room.players:
                user_id = player.get("user_id")
                user_name = player.get("user_name", "匿名")

                # 聚合该学生在该房间的数据
                my_clues = [c for c in room.clues_log if getattr(c, "player_id", None) == user_id]
                my_questions = [q for q in room.questions_log if getattr(q, "player_id", None) == user_id]
                my_negations = [q for q in room.negation_board if getattr(q, "player_id", None) == user_id]
                my_combos = [c for c in room.combo_history if getattr(c, "player_id", None) == user_id]

                clues = len(my_clues)
                questions = len(my_questions)
                negations = len(my_negations)
                combos = len([c for c in my_combos if getattr(c, "success", True)])
                layers = len(room.unlocked_layers)

                # 评分公式
                score = clues * 10 + combos * 25 - negations * 5 + layers * 30

                leaderboard.append({
                    "user_id": user_id,
                    "user_name": user_name,
                    "room_id": room.room_id,
                    "room_phase": room.phase.value if hasattr(room.phase, "value") else str(room.phase),
                    "clues": clues,
                    "questions_asked": questions,
                    "negations": negations,
                    "combos": combos,
                    "layers_unlocked": layers,
                    "total_score": score,
                })

        # 排序
        if sort_by == "clues":
            leaderboard.sort(key=lambda x: (-x["clues"], x["negations"]))
        elif sort_by == "combos":
            leaderboard.sort(key=lambda x: (-x["combos"], x["negations"]))
        elif sort_by == "negations":
            leaderboard.sort(key=lambda x: x["negations"])  # 越少越好
        elif sort_by == "layers":
            leaderboard.sort(key=lambda x: (-x["layers_unlocked"], -x["combos"]))
        else:
            sort_by = "total_score"
            leaderboard.sort(key=lambda x: -x["total_score"])

        # 加排名 + 奖牌
        for idx, entry in enumerate(leaderboard):
            entry["rank"] = idx + 1
            if idx == 0:
                entry["badge"] = "🥇"
            elif idx == 1:
                entry["badge"] = "🥈"
            elif idx == 2:
                entry["badge"] = "🥉"
            else:
                entry["badge"] = "🎖️"

        return {
            "rankings": leaderboard,
            "total_students": len(leaderboard),
            "sort_by": sort_by,
        }

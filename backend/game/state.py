"""汤探局 - 房间状态机与单例数据"""
import uuid
import time
import threading
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


class GamePhase(str, Enum):
    """7阶段游戏状态机"""
    LOBBY = "lobby"                  # 等人
    INTRO = "intro"                  # 阶段1: 开局前置
    QUESTIONING = "questioning"      # 阶段2: 海龟汤定向提问
    CARD_PLAY = "card_play"          # 阶段3-4: 单武将/合技
    REVEAL = "reveal"                # 阶段5: 终极揭晓
    DEBRIEF = "debrief"              # 阶段6: 即时分段复盘
    EXTEND = "extend"                # 阶段7: 课后拓展
    END = "end"


LAYER_ORDER = ["phenomenon", "condition", "microscopic", "ultimate"]


@dataclass
class QARecord:
    """一条提问记录"""
    qid: str
    category: str
    text: str
    answer: str          # 是 / 否 / 相关 / 无法判断
    hint: str
    knowledge_point: str
    timestamp: float
    player_id: str = ""   # 谁提的（双人协作模式）


@dataclass
class ClueRecord:
    """一条线索记录"""
    clue_id: str
    card_id: str
    label: str
    content: str
    knowledge_point: str
    layer: Optional[str] = None  # 归属层级（解锁后填入）
    player_id: str = ""   # 谁出的卡


@dataclass
class Room:
    """一个房间的完整状态"""
    room_id: str
    players: List[Dict[str, str]] = field(default_factory=list)   # [{user_id, user_name}]
    phase: GamePhase = GamePhase.LOBBY
    questions_remaining: int = 5
    card_usage: Dict[str, int] = field(default_factory=dict)              # 全局累计 card_id -> 用了几次（向后兼容）
    per_player_card_usage: Dict[str, Dict[str, int]] = field(default_factory=dict)  # 双人: player_id -> {card_id: n}
    questions_per_player: Dict[str, int] = field(default_factory=dict)    # player_id -> 剩余提问次数
    unlocked_layers: List[str] = field(default_factory=list)
    negation_board: List[QARecord] = field(default_factory=list)
    questions_log: List[QARecord] = field(default_factory=list)
    clues_log: List[ClueRecord] = field(default_factory=list)
    combo_history: List[Dict[str, Any]] = field(default_factory=list)
    turn_player_id: str = ""    # 现在轮到谁（空=不限/单玩家）
    created_at: float = field(default_factory=time.time)
    last_active_at: float = field(default_factory=time.time)
    is_multiplayer: bool = False

    def current_player(self) -> Optional[Dict[str, str]]:
        if not self.is_multiplayer:
            return self.players[0] if self.players else None
        for p in self.players:
            if p["user_id"] == self.turn_player_id:
                return p
        return None

    def other_player(self) -> Optional[Dict[str, str]]:
        if not self.is_multiplayer:
            return None
        for p in self.players:
            if p["user_id"] != self.turn_player_id:
                return p
        return None

    def advance_turn(self) -> None:
        """双人模式轮换 turn_player_id；单人不变。"""
        if not self.is_multiplayer or len(self.players) < 2:
            return
        ids = [p["user_id"] for p in self.players]
        if self.turn_player_id in ids:
            idx = ids.index(self.turn_player_id)
            self.turn_player_id = ids[(idx + 1) % len(ids)]
        else:
            self.turn_player_id = ids[0]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_id": self.room_id,
            "players": self.players,
            "phase": self.phase.value,
            "questions_remaining": self.questions_remaining,
            "card_usage": self.card_usage,
            "per_player_card_usage": self.per_player_card_usage,
            "questions_per_player": self.questions_per_player,
            "unlocked_layers": self.unlocked_layers,
            "is_multiplayer": self.is_multiplayer,
            "turn_player_id": self.turn_player_id,
            "current_player": self.current_player(),
            "other_player": self.other_player(),
            "negation_board": [
                {"id": q.qid, "text": q.text, "answer": q.answer,
                 "knowledge_point": q.knowledge_point, "player_id": q.player_id}
                for q in self.negation_board
            ],
            "questions_log": [
                {"id": q.qid, "category": q.category, "text": q.text, "answer": q.answer,
                 "knowledge_point": q.knowledge_point, "player_id": q.player_id}
                for q in self.questions_log
            ],
            # P1 #12：clues_log 同时返回 content（已出过的线索可回看）
            "clues_log": [
                {"clue_id": c.clue_id, "card_id": c.card_id, "label": c.label,
                 "content": c.content, "knowledge_point": c.knowledge_point,
                 "layer": c.layer, "player_id": c.player_id}
                for c in self.clues_log
            ],
            "combo_history": self.combo_history,
        }


class RoomManager:
    """房间管理器（单例）

    释放/P1 #10：
    - 房间带 ttl_seconds 默认 30 分钟
    - 启动后台守护线程 gc_expired() 定期清理
    - touch() 刷新房间活动时间
    """

    DEFAULT_TTL_SECONDS = 30 * 60  # 30 分钟
    GC_INTERVAL_SECONDS = 60

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS):
        self._rooms: Dict[str, Room] = {}
        self._ttl = ttl_seconds
        self._gc_thread: Optional[threading.Thread] = None
        self._gc_stop = threading.Event()
        self._start_gc()

    def _start_gc(self) -> None:
        if self._gc_thread and self._gc_thread.is_alive():
            return
        t = threading.Thread(target=self._gc_loop, daemon=True, name="RoomManagerGC")
        self._gc_thread = t
        t.start()

    def _gc_loop(self) -> None:
        while not self._gc_stop.wait(self.GC_INTERVAL_SECONDS):
            self.gc_expired()

    def touch(self, room_id: str) -> None:
        """刷新房间活动时间（LOBBY 阶段不刷新，避免等人房间被清）"""
        r = self._rooms.get(room_id)
        if r and r.phase != GamePhase.LOBBY:
            r.last_active_at = time.time()

    def gc_expired(self) -> List[str]:
        """清理过期房间，返回被清掉的 room_id 列表"""
        now = time.time()
        expired = [
            rid for rid, r in self._rooms.items()
            if (now - r.last_active_at) > self._ttl
        ]
        for rid in expired:
            self._rooms.pop(rid, None)
        return expired

    def rejoin(self, room_id: str, player_id: str) -> Optional[Room]:
        """P1 #10：按 player_id 找回身份（只改房间内字段，不动状态机）"""
        room = self._rooms.get(room_id)
        if not room:
            return None
        if any(p["user_id"] == player_id for p in room.players):
            return room
        return None

    def create_room(self, user_name: str, max_questions: int = 10) -> Room:
        """单玩家快速开局（向后兼容）。"""
        room = Room(room_id=str(uuid.uuid4())[:8])
        uid = str(uuid.uuid4())[:8]
        room.players.append({"user_id": uid, "user_name": user_name})
        room.phase = GamePhase.INTRO
        room.questions_remaining = max_questions
        room.questions_per_player[uid] = max_questions
        room.turn_player_id = uid
        self._rooms[room.room_id] = room
        return room

    def create_multiplayer_room(self, user_name: str, max_questions: int = 10) -> Room:
        """G3 双人协作房间：LOBBY 阶段，等第二个玩家 join。"""
        room = Room(room_id=str(uuid.uuid4())[:8])
        uid = str(uuid.uuid4())[:8]
        room.players.append({"user_id": uid, "user_name": user_name})
        room.questions_remaining = max_questions
        room.questions_per_player[uid] = max_questions
        room.is_multiplayer = True
        room.turn_player_id = uid
        room.phase = GamePhase.LOBBY
        self._rooms[room.room_id] = room
        return room

    def join_room(self, room_id: str, user_name: str) -> Optional[Room]:
        """G3：第二个玩家加入。返回房间（如果满了/不存在返 None）。"""
        room = self._rooms.get(room_id)
        if not room:
            return None
        if not room.is_multiplayer:
            return None
        if len(room.players) >= 2:
            return None  # 已满
        uid = str(uuid.uuid4())[:8]
        room.players.append({"user_id": uid, "user_name": user_name})
        # 第二玩家也使用与房主相同的提问额度（从 questions_remaining 取，保持同步）
        mp = room.questions_remaining or 10
        room.questions_per_player[uid] = mp
        # 两个人都到齐了 → INTRO 阶段，turn 切到第 1 位
        if len(room.players) == 2:
            room.phase = GamePhase.INTRO
            room.turn_player_id = room.players[0]["user_id"]
        return room

    def get_room(self, room_id: str) -> Optional[Room]:
        return self._rooms.get(room_id)

    def remove_room(self, room_id: str):
        self._rooms.pop(room_id, None)

    def list_rooms(self) -> List[str]:
        return list(self._rooms.keys())


def next_layer(current_layers: List[str]) -> Optional[str]:
    """按层级顺序返回下一层，未通则返回已解锁最后一层"""
    for layer in LAYER_ORDER:
        if layer not in current_layers:
            return None  # 还有未解锁
    return "ultimate"


def is_layer_unlocked(room: Room, layer: str) -> bool:
    return layer in room.unlocked_layers


def prev_layer(layer: str) -> Optional[str]:
    """上一层是哪层（用于层锁校验）"""
    try:
        idx = LAYER_ORDER.index(layer)
    except ValueError:
        return None
    if idx == 0:
        return None
    return LAYER_ORDER[idx - 1]


def get_player_for_request(room: Room, user_id: Optional[str]) -> Optional[Dict[str, str]]:
    """双人模式：校验 user_id 是否属于该房间。"""
    if not user_id:
        return room.players[0] if room.players else None
    for p in room.players:
        if p["user_id"] == user_id:
            return p
    return None

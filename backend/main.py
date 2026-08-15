"""汤探局 - FastAPI main entry (rewritten)"""
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from game.state import RoomManager, GamePhase, Room
from game.engine import GameEngine
from game.questions import QuestionJudge
from game.deck import DeckEngine

# ============ Logging (P2 #15) ============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("tangtanju")

# ============ 前端静态目录探测（必须在 app 创建前完成）============
SERVE_STATIC = os.getenv("SERVE_STATIC", "") == "1" or os.getenv("RAILWAY_ENVIRONMENT") is not None

_BACKEND_DIR = Path(__file__).parent
_CANDIDATE_STATIC_DIRS = [
    _BACKEND_DIR / "static",                        # 部署产物位置（Dockerfile 会拷到这里）
    _BACKEND_DIR.parent / "frontend" / "dist",      # 本地结构
]

STATIC_DIR: Optional[Path] = None
if SERVE_STATIC:
    for d in _CANDIDATE_STATIC_DIRS:
        if d.exists() and (d / "index.html").exists():
            STATIC_DIR = d
            break
    if STATIC_DIR:
        logger.info("Serving frontend from %s (SPA fallback enabled)", STATIC_DIR)
    else:
        logger.warning("SERVE_STATIC=1 but no static dir found in %s", _CANDIDATE_STATIC_DIRS)
else:
    logger.info("Frontend static serving disabled (dev mode). Set SERVE_STATIC=1 to enable.")

app = FastAPI(title="汤探局 API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Data ============
DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(name: str) -> Dict[str, Any]:
    """P2 #16：每次调用重新读盘（dev 模式可热重载），生产可改回模块级缓存。

    Bug 修复：data/*.json 混合 UTF-8 / GBK + 多种损坏模式：
      1. 手写 JSON 包含 raw \\n / \\t (用 strict=False 容忍)
      2. UTF-8 BOM 头 (0xEF 0xBB 0xBF)
      3. salt_lake_fossil.json 双重编码：GBK 字节被 UTF-8 解读，看成乱码
      4. 部分字符串闭合双引号被替换成 ? (损坏模式 ` '?` → `"`)
      5. 文件中夹杂孤儿 0x3F 字节（不是真引号损坏，不要一律替换）
      6. "?" 后直接换行 / 其他字符也是损坏 (line 63 bloom_level)
    容错策略：
      a. 先按 UTF-8 / GBK 尝试解码 + strict=False
      b. 字节级修复：把任何 '?' 后紧跟 JSON 结构性字符 (,]} \n\r)的 '?' 改成 '"'
      c. 最后兑底：errors='replace' + json strict=False
    """
    import json as _json
    p = DATA_DIR / name
    raw = p.read_bytes()
    # 去 BOM（utf-8-sig 会自动处理，但手动兜底更安全）
    if raw.startswith(b'\xef\xbb\xbf'):
        raw = raw[3:]
    # 字节级修复：损坏的字符串闭合 '?' 后跟 JSON 结构字符 (,]} \n\r) 全部改为 '"'
    # 损坏模式枚举：
    fixed = raw
    # 1. ?", → ","
    fixed = fixed.replace(b'?",', b'",')
    fixed = fixed.replace(b'?",\n', b'",\n')
    fixed = fixed.replace(b'?",\r\n', b'",\r\n')
    # 2. ?, → ", (但不动 ? 后接字母/数字/汉字，这些是真数据)
    fixed = fixed.replace(b'?,', b'",')
    fixed = fixed.replace(b'?,\n', b'",\n')
    fixed = fixed.replace(b'?,\r\n', b'",\r\n')
    fixed = fixed.replace(b'?, ', b'", ')
    # 3. ?] → "]
    fixed = fixed.replace(b'?]', b'"]')
    fixed = fixed.replace(b'?]\n', b'"]\n')
    fixed = fixed.replace(b'?]\r\n', b'"]\r\n')
    # 4. ?} → "}
    fixed = fixed.replace(b'?}', b'"}')
    fixed = fixed.replace(b'?}\n', b'"}\n')
    fixed = fixed.replace(b'?}\r\n', b'"}r\n')
    # 5. ?: (对象后面) → ":
    fixed = fixed.replace(b'?:', b'":')
    # 6. ? 后面接空白后 key (line 63 场景：? 后直接 \n)
    fixed = fixed.replace(b'?\n  "', b'"\n  "')  # line 64-65 边界
    fixed = fixed.replace(b'?\n    "', b'"\n    "')  # line 67-68 边界
    fixed = fixed.replace(b'?\n', b'"\n')  # 通用：? 后 \n
    # 7. ? 直接接 } 不可能（关闭引号后才 }, 这里不需要修复 ?} 以外）
    # 尝试多种编码解码 (使用 errors='replace' 以避免 invalid byte 猏取)
    # 优先 UTF-8: 现在 salt_lake_fossil.json 已经是干净 UTF-8 文件
    # 倒退以 GBK/GB18030 作为兑底 (仅在 UTF-8 失败后尝试)
    for enc in ("utf-8", "gb18030", "gbk"):
        try:
            # 使用 replace 错误处理避免猏取 invalid bytes
            txt = fixed.decode(enc, errors='replace')
            result = _json.loads(txt, strict=False)
            # 如果是 GBK 解码结果, 应该主要是中文 (U+4E00-U+9FFF)
            # 如果 UTF-8 解码结果里面有 大量 U+0080-U+00FF (latin-1 view of GBK bytes),
            # 那说明这是 UTF-8 错读 GBK bytes, 结果是 mojibake, 跳过
            if enc == 'utf-8':
                # 检查是不是 mojibake: 字符串含较多 U+0080-U+00FF
                sample_strs = [str(result.get('case_title', ''))]
                for layer in result.get('layers', {}).values():
                    if isinstance(layer, dict):
                        sample_strs.append(str(layer.get('name', '')))
                        sample_strs.append(str(layer.get('reveal_text', '')[:100]))
                mojibake_count = 0
                total_count = 0
                for s in sample_strs:
                    for c in s:
                        total_count += 1
                        if 0x80 <= ord(c) <= 0xFF:
                            mojibake_count += 1
                if total_count > 0 and mojibake_count / total_count > 0.3:
                    # UTF-8 解读出了 mojibake, 跳过
                    continue
            return result
        except _json.JSONDecodeError as e:
            continue
        except (UnicodeDecodeError, LookupError) as e:
            continue
    # 最后兑底 (不应走到这里)
    raise RuntimeError(f"Failed to load JSON for {name}")


# 模块级缓存，启动时加载一次（dev_reload 端点可强制刷新）
SCRIPT = _load_json("salt_lake_fossil.json")
CARDS = _load_json("generals_highschool.json")
QUESTIONS = _load_json("questions_salt_lake.json")
KNOWLEDGE = _load_json("knowledge_map.json")

deck_engine = DeckEngine(CARDS, SCRIPT)
game_engine = GameEngine(SCRIPT, CARDS)
question_judge = QuestionJudge(QUESTIONS)
room_manager = RoomManager()


def reload_data() -> Dict[str, Any]:
    """P2 #16：dev 用重启文件后调用此函数刷新所有内存数据。"""
    global SCRIPT, CARDS, QUESTIONS, KNOWLEDGE, deck_engine, game_engine, question_judge
    try:
        SCRIPT = _load_json("salt_lake_fossil.json")
        CARDS = _load_json("generals_highschool.json")
        QUESTIONS = _load_json("questions_salt_lake.json")
        KNOWLEDGE = _load_json("knowledge_map.json")
    except Exception as e:
        logger.exception("reload_data JSON parse failed: %s", e)
        raise HTTPException(500, f"data parse failed: {e}")
    try:
        deck_engine = DeckEngine(CARDS, SCRIPT)
        game_engine = GameEngine(SCRIPT, CARDS)
        question_judge = QuestionJudge(QUESTIONS)
    except Exception as e:
        logger.exception("reload_data engine init failed: %s", e)
        raise HTTPException(500, f"engine init failed: {e}")
    return {"ok": True, "reloaded": ["script", "cards", "questions", "knowledge"]}


def _normalize_script_text(s: Any) -> Any:
    """将 GBK mojibake 字符串转成 UTF-8 可读中文。

    原理: salt_lake_fossil.json 里的中文字符串在文件中是 GBK 双字节序列,
    Python 用 UTF-8 解码后, 每个 GBK 字节变成 1 个 Unicode 码点 (U+0080 ~ U+00FF),
    也就是说, 当前 SCRIPT['case_title'] 的字符串里「每 2 个 Unicode 字符对应一个中文字」。

    修复: 将字符串重新以 latin-1 编码 (单字节可逆) → GBK 解码 → UTF-8 输出。
    """
    if not isinstance(s, str):
        return s
    if len(s) == 0:
        return s
    # 检测是否是 mojibake: 大量字符码点在 0x80-0xFF (GBK 字节被当 UTF-8 char)
    high_count = sum(1 for c in s if 0x80 <= ord(c) <= 0xFF)
    if high_count / len(s) < 0.5:
        return s  # 看起来不是 mojibake, 不动
    try:
        # 将字符串以 latin-1 编码 → 拿到原始字节序列
        raw_bytes = s.encode('latin-1')
        # 用 GBK 解码这些字节
        decoded = raw_bytes.decode('gbk', errors='replace')
        # 验证: 解码后应该有 CJK 字符 (U+4E00-U+9FFF) 和可见字符, 不是 latin-1 字符 (U+0080-U+00FF)
        cjk_count = sum(1 for c in decoded if 0x4E00 <= ord(c) <= 0x9FFF)
        # 如果解码后含有 CJK chars, 说明解码成功 (GBK → UTF-8)
        if cjk_count > 0:
            return decoded
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return s


def _normalize_script_obj(obj: Any) -> Any:
    """递归遍历 dict/list, 把字符串走 _normalize_script_text。"""
    if isinstance(obj, dict):
        return {k: _normalize_script_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalize_script_obj(v) for v in obj]
    return _normalize_script_text(obj)


# 启动时 normalize 一次（静态）
SCRIPT = _normalize_script_obj(SCRIPT)


# ============ WebSocket Manager (P0 #2 修复) ============
class WSManager:
    def __init__(self):
        self.active: Dict[str, List[Any]] = {}

    async def broadcast(self, room_id: str, msg: dict) -> None:
        sockets = list(self.active.get(room_id, []))
        if not sockets:
            return
        dead: List[Any] = []
        for ws in sockets:
            try:
                await ws.send_json(msg)
            except Exception as e:
                logger.debug("ws send failed room=%s: %s", room_id, e)
                dead.append(ws)
        if dead:
            for d in dead:
                try:
                    await d.close()
                except Exception:
                    pass
            # 结构化移除死连接（避免双重 GC + 双重释放）
            self.active[room_id] = [
                s for s in self.active.get(room_id, []) if s not in dead
            ]
            self._gc_room(room_id)

    def disconnect(self, room_id: str, ws) -> None:
        if room_id not in self.active:
            return
        try:
            self.active[room_id].remove(ws)
        except ValueError:
            pass
        self._gc_room(room_id)

    def _gc_room(self, room_id: str) -> None:
        if room_id in self.active and not self.active[room_id]:
            self.active.pop(room_id, None)


ws_mgr = WSManager()


async def broadcast(room_id: str, msg: dict) -> None:
    await ws_mgr.broadcast(room_id, msg)


# ============ Public data endpoints ============
@app.get("/")
def root():
    # 生产环境（SPA 静态文件可用了）下，根路径返回前端 index.html
    if STATIC_DIR is not None:
        idx = STATIC_DIR / "index.html"
        if idx.exists():
            return FileResponse(str(idx))
    # 否则返回 JSON API 概要（便于手动探测服务是否存活）
    return {
        "name": "汤探局·SaltLake Detective",
        "version": "1.0",
        "case": SCRIPT.get("case_title"),
        "status": "running",
        "endpoints": [
            "/api/script", "/api/cards", "/api/questions", "/api/knowledge",
            "/api/room/create", "/api/room/state/{room_id}",
            "/api/ask", "/api/card/use", "/api/card/combo",
            "/api/room/phase", "/api/room/reveal", "/api/room/debrief", "/api/room/extend",
            "/api/room/rejoin", "/api/dev/reset_cards", "/api/dev/reload_data",
        ],
    }


@app.get("/api/script")
def get_script():
    return SCRIPT


@app.get("/api/cards")
def get_cards(reveal: bool = False):
    """U1/U2 spoiler-safe: hide clue content unless reveal=true."""
    if reveal:
        return CARDS
    safe_cards = []
    for c in CARDS.get("cards", []):
        safe_cards.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "title": c.get("title"),
            "category": c.get("category"),
            "skill_name": c.get("skill_name"),
            "skill_text": c.get("skill_text"),
            "subject": c.get("subject"),
            "max_use": c.get("max_use", 1),
            "combo_partner": c.get("combo_partner"),
            "combo_unlock_layer": c.get("combo_unlock_layer"),
            "badge_icon": c.get("badge_icon"),
            "clue_count": len(c.get("clues", [])),
            "clues": [
                {"id": clue.get("id"), "label": clue.get("label"),
                 "knowledge_point": clue.get("knowledge_point")}
                for clue in c.get("clues", [])
            ],
        })
    return {"cards": safe_cards}


@app.get("/api/questions")
def get_questions():
    """U1 spoiler-safe: return questions WITHOUT answer field."""
    return {
        "questions": question_judge.list_questions(public_only=True)
    }


@app.get("/api/card/clue")
def get_card_clue(room_id: str, card_id: str, idx: int):
    """U1 fix: only return clue content when player has actually used the card."""
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(404, "房间不存在")
    # P1 #8：以 per_player 为唯一真源（单人归 player 0）
    me = room.players[0]["user_id"] if room.players else ""
    used = room.per_player_card_usage.get(me, {}).get(card_id, 0)
    if used <= idx:
        raise HTTPException(403, f"尚未出牌至第 {idx + 1} 次，无法查看该线索")
    room_manager.touch(room_id)
    return {"ok": True, "clue": deck_engine.get_clue_at_index(card_id, idx)}


@app.get("/api/knowledge")
def get_knowledge():
    return KNOWLEDGE


# ============ Health check (部署用) ============
@app.get("/api/health")
def health():
    """Railway / Docker 健康检查：永远返回 200 + 关键状态。"""
    return {
        "ok": True,
        "service": "tangtanju-api",
        "version": app.version,
        "data_loaded": bool(SCRIPT and CARDS and QUESTIONS and KNOWLEDGE),
        "rooms_active": len(room_manager.rooms) if hasattr(room_manager, "rooms") else 0,
    }


# ============ Room endpoints ============
class CreateRoomReq(BaseModel):
    user_name: str
    player_id: Optional[str] = None


@app.post("/api/room/create")
def create_room(req: CreateRoomReq):
    max_q = game_engine.script.get("max_questions", 10) if game_engine else 10
    room = room_manager.create_room(req.user_name, max_questions=max_q)
    return {"ok": True, "room": room.to_dict(), "room_id": room.room_id,
            "player_id": room.players[0]["user_id"]}


class MultiplayerCreateReq(BaseModel):
    user_name: str


@app.post("/api/room/multiplayer")
def create_multiplayer(req: MultiplayerCreateReq):
    max_q = game_engine.script.get("max_questions", 10) if game_engine else 10
    room = room_manager.create_multiplayer_room(req.user_name, max_questions=max_q)
    return {"ok": True, "room": room.to_dict(), "room_id": room.room_id,
            "player_id": room.players[0]["user_id"], "waiting": room.phase == GamePhase.LOBBY}


class JoinRoomReq(BaseModel):
    room_id: str
    user_name: str


@app.post("/api/room/join")
def join_room(req: JoinRoomReq):
    room = room_manager.join_room(req.room_id, req.user_name)
    if not room:
        raise HTTPException(404, "房间不存在或未开放加入")
    if len(room.players) > 2:
        raise HTTPException(400, "房间已满")
    me = room.players[-1]
    room_manager.touch(req.room_id)
    return {"ok": True, "room": room.to_dict(), "player_id": me["user_id"]}


# ============ P1 #10：重连 ============
class RejoinReq(BaseModel):
    room_id: str
    player_id: str


@app.post("/api/room/rejoin")
def rejoin(req: RejoinReq):
    """按 player_id 找回身份（双人模式必备）。"""
    room = room_manager.rejoin(req.room_id, req.player_id)
    if not room:
        raise HTTPException(404, "房间不存在或玩家不在该房间")
    if room.is_multiplayer:
        room_manager.touch(req.room_id)
    return {"ok": True, "room": room.to_dict(), "player_id": req.player_id}


# ============ Ask / Card / Combo ============
class AskReq(BaseModel):
    room_id: str
    qid: str
    player_id: Optional[str] = None


@app.post("/api/ask")
def ask_question(req: AskReq):
    room = room_manager.get_room(req.room_id)
    if not room:
        raise HTTPException(404, "房间不存在")
    err = game_engine._verify_turn(room, req.player_id)
    if err:
        raise HTTPException(403, err["error"])
    result = game_engine.ask_question(room, req.qid, question_judge, req.player_id)
    if "error" in result:
        raise HTTPException(400, result["error"])
    room_manager.touch(req.room_id)
    return {"ok": True, **result}


class UseCardReq(BaseModel):
    room_id: str
    card_id: str
    player_id: Optional[str] = None


@app.post("/api/card/use")
def use_card(req: UseCardReq):
    room = room_manager.get_room(req.room_id)
    if not room:
        raise HTTPException(404, "房间不存在")
    err = game_engine._verify_turn(room, req.player_id)
    if err:
        raise HTTPException(403, err["error"])
    result = game_engine.play_single_card(room, req.card_id, deck_engine, req.player_id)
    if "error" in result:
        raise HTTPException(400, result["error"])
    room_manager.touch(req.room_id)
    return {"ok": True, **result}


class ComboReq(BaseModel):
    room_id: str
    cards: List[str]
    player_id: Optional[str] = None


@app.post("/api/card/combo")
def combo(req: ComboReq):
    room = room_manager.get_room(req.room_id)
    if not room:
        raise HTTPException(404, "房间不存在")
    err = game_engine._verify_turn(room, req.player_id)
    if err:
        raise HTTPException(403, err["error"])
    result = game_engine.try_unlock_layer(room, req.cards, deck_engine, req.player_id)
    if "error" in result:
        raise HTTPException(400, result["error"])
    room_manager.touch(req.room_id)
    return {"ok": True, **result}


# ============ P2 #14: state 合并 cards + questions 一次拿齐 ============
@app.get("/api/room/state/{room_id}")
def room_state(room_id: str, include_static: bool = False):
    """include_static=true 时同时返回 cards/questions/knowledge（前端省一次 RTT）。"""
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(404, "房间不存在")
    if room.is_multiplayer:
        room_manager.touch(room_id)
    out: Dict[str, Any] = {"room": game_engine.get_state(room)}
    if include_static:
        out["cards"] = CARDS.get("cards", [])
        out["questions"] = question_judge.list_questions(public_only=True)
        out["knowledge"] = KNOWLEDGE
    return out


class PhaseReq(BaseModel):
    room_id: str
    target: str


@app.post("/api/room/phase")
def set_phase(req: PhaseReq):
    room = room_manager.get_room(req.room_id)
    if not room:
        raise HTTPException(404, "房间不存在")
    try:
        room.phase = GamePhase(req.target)
    except ValueError:
        raise HTTPException(400, f"未知阶段: {req.target}")
    room_manager.touch(req.room_id)
    return {"ok": True, "phase": room.phase.value}


class RoomReq(BaseModel):
    room_id: str


@app.post("/api/room/reveal")
def room_reveal(req: RoomReq):
    room = room_manager.get_room(req.room_id)
    if not room:
        raise HTTPException(404, "房间不存在")
    return {"ok": True, **game_engine.reveal_ultimate(room)}


@app.post("/api/room/debrief")
def room_debrief(req: RoomReq):
    room = room_manager.get_room(req.room_id)
    if not room:
        raise HTTPException(404, "房间不存在")
    return {"ok": True, **game_engine.to_debrief(room)}


@app.post("/api/room/extend")
def room_extend(req: RoomReq):
    room = room_manager.get_room(req.room_id)
    if not room:
        raise HTTPException(404, "房间不存在")
    return {"ok": True, **game_engine.to_extend(room)}


# ============ Dev-only ============
@app.post("/api/dev/reset_cards")
async def dev_reset_cards(request: Request):
    """Dev-only: clear card_usage for the room."""
    body = await request.json()
    room_id = body.get("room_id")
    if not room_id:
        raise HTTPException(400, "missing room_id")
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(404, "room not found")
    room.card_usage.clear()
    room.per_player_card_usage.clear()
    return {"ok": True, "message": "武将卡已重置"}


@app.post("/api/dev/reload_data")
def dev_reload_data():
    """P2 #16：刷新内存中的 JSON（无需重启）。"""
    return reload_data()


@app.post("/api/dev/gc_rooms")
def dev_gc_rooms():
    """手动触发 GC（默认 60s 自动跑）"""
    expired = room_manager.gc_expired()
    return {"ok": True, "expired": expired}


# ============ WebSocket ============
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    ws_mgr.active.setdefault(room_id, []).append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            room = room_manager.get_room(room_id)
            if not room:
                await websocket.send_json({"ok": False, "error": "room not found"})
                continue
            response: Dict[str, Any] = {"ok": True, "action": action}
            player_id = data.get("player_id")

            if action == "ask":
                err = game_engine._verify_turn(room, player_id)
                if err:
                    response = {"ok": False, "error": err["error"]}
                else:
                    result = game_engine.ask_question(room, data.get("qid"), question_judge, player_id)
                    response.update(result)

            elif action == "use_card":
                err = game_engine._verify_turn(room, player_id)
                if err:
                    response = {"ok": False, "error": err["error"]}
                else:
                    result = game_engine.play_single_card(room, data.get("card_id"), deck_engine, player_id)
                    response.update(result)

            elif action == "combo":
                err = game_engine._verify_turn(room, player_id)
                if err:
                    response = {"ok": False, "error": err["error"]}
                else:
                    result = game_engine.try_unlock_layer(room, data.get("cards", []), deck_engine, player_id)
                    response.update(result)

            elif action == "set_phase":
                try:
                    room.phase = GamePhase(data.get("target"))
                except ValueError:
                    response = {"ok": False, "error": "unknown phase"}

            elif action == "reveal":
                response.update(game_engine.reveal_ultimate(room))

            elif action == "debrief":
                response.update(game_engine.to_debrief(room))

            elif action == "extend":
                response.update(game_engine.to_extend(room))

            else:
                response = {"ok": False, "error": f"unknown action: {action}"}

            await websocket.send_json(response)
            # 广播最新状态给所有在线客户端
            try:
                room_manager.touch(room_id)
            except Exception:
                pass
            state_msg = {"action": "state_update", "state": game_engine.get_state(room)}
            await broadcast(room_id, state_msg)

    except WebSocketDisconnect:
        logger.info("ws disconnect room=%s", room_id)
    except Exception as e:
        logger.exception("ws error room=%s: %s", room_id, e)
    finally:
        try:
            ws_mgr.disconnect(room_id, websocket)
        except (ValueError, KeyError):
            pass


# ============ 教师端 Dashboard API (P1) ============
# 教师端不修改 RoomManager 核心逻辑，只做数据聚合 + 课堂控制
from teacher import TeacherDashboard  # noqa: E402

_teacher_dashboard = TeacherDashboard(room_manager, SCRIPT, CARDS)


class TeacherOverviewResp(BaseModel):
    """班级总览响应"""
    teacher_id: Optional[str] = None
    timestamp: str
    total_rooms: int
    active_rooms: int
    total_students: int
    rooms_detail: list
    aggregated: dict


@app.get("/api/teacher/overview", response_model=TeacherOverviewResp,
         summary="教师端：班级进度总览")
def teacher_overview(teacher_id: Optional[str] = None):
    """获取所有活跃房间的进度汇总，用于教师 Dashboard 主页"""
    return _teacher_dashboard.get_class_overview(teacher_id)


@app.get("/api/teacher/rooms", summary="教师端：列出所有房间")
def teacher_rooms(teacher_id: Optional[str] = None):
    """列出所有活跃房间（带学生、阶段、进度）"""
    return _teacher_dashboard.get_class_overview(teacher_id).get("rooms_detail", [])


@app.get("/api/teacher/kp_catalog", summary="教师端：14 考点掌握率")
def teacher_kp_catalog():
    """返回 14 个考点的当前班级掌握率"""
    return _teacher_dashboard.get_kp_catalog()


@app.get("/api/teacher/student/{room_id}/{user_id}", summary="教师端：学情画像")
def teacher_student_profile(room_id: str, user_id: str):
    """单个学生在某房间的完整学情画像（能力雷达 + 否决模式 + 时间线）"""
    profile = _teacher_dashboard.get_student_profile(room_id, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="学生或房间不存在")
    return profile


@app.get("/api/teacher/heatmap/{room_id}", summary="教师端：答题热力图")
def teacher_heatmap(room_id: str):
    """单个房间的答题热力图数据 + 卡住学生建议"""
    return _teacher_dashboard.get_question_heatmap(room_id)


# ---- 课堂控制 ----
class ControlAction(BaseModel):
    teacher_id: str
    message: Optional[str] = None
    user_id: Optional[str] = None


@app.post("/api/teacher/pause/{room_id}", summary="教师端：暂停房间")
def teacher_pause(room_id: str, body: ControlAction):
    """暂停指定房间（学生端会收到 paused=true 事件）"""
    return _teacher_dashboard.pause_room(room_id, body.teacher_id)


@app.post("/api/teacher/resume/{room_id}", summary="教师端：恢复房间")
def teacher_resume(room_id: str, body: ControlAction):
    return _teacher_dashboard.resume_room(room_id, body.teacher_id)


@app.post("/api/teacher/broadcast/{room_id}", summary="教师端：广播消息")
def teacher_broadcast(room_id: str, body: ControlAction):
    """向房间内所有学生广播一条教师消息（学生端会弹 toast）"""
    if not body.message:
        raise HTTPException(status_code=400, detail="message 不能为空")
    return _teacher_dashboard.broadcast_message(room_id, body.teacher_id, body.message)


@app.post("/api/teacher/kick/{room_id}", summary="教师端：踢出学生")
def teacher_kick(room_id: str, body: ControlAction):
    """踢出指定学生（用于课堂纪律管理）"""
    if not body.user_id:
        raise HTTPException(status_code=400, detail="user_id 不能为空")
    return _teacher_dashboard.kick_student(room_id, body.teacher_id, body.user_id)


@app.get("/api/teacher/control/{room_id}", summary="学生端：拉取课堂控制状态")
def teacher_control_state(room_id: str):
    """学生端轮询此接口，检测是否被暂停 / 收到广播 / 被踢出"""
    return _teacher_dashboard.get_control_state(room_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ============ 静态资源 + SPA Fallback（必须放在所有 /api 路由之后）============
if STATIC_DIR is not None:
    assets_dir = STATIC_DIR / "assets"

    # 带 hash 的静态资源走 StaticFiles（高效 + 正确处理 MIME）
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    # 兜底 favicon
    @app.get("/favicon.ico", include_in_schema=False)
    def _favicon():
        f = STATIC_DIR / "favicon.ico"
        if f.exists():
            return FileResponse(str(f))
        return JSONResponse({}, status_code=404)

    # SPA fallback：只要路径不是以 api/ 或 ws/ 开头，就返回前端
    # 之前所有 @app.get 路径都已被匹配，这里捕获未命中的 Vue history 路径
    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        # 先试一下直接命中的静态文件（多 404 没事）
        candidate = STATIC_DIR / full_path
        if candidate.is_file():
            return FileResponse(str(candidate))
        # Vue history 模式 fallback
        index_html = STATIC_DIR / "index.html"
        return FileResponse(str(index_html))

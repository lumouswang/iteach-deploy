"""pytest 公共 fixture：构造完整应用 + RoomManager。"""
import sys
from pathlib import Path

# 把 backend/ 加到 sys.path，能 `import game.xxx`
BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

import pytest
from main import (
    app,
    SCRIPT,
    CARDS,
    QUESTIONS,
    room_manager,
    game_engine,
    question_judge,
    deck_engine,
)

# 与生产一致：房间提问上限取自 script 的 max_questions（当前为 9）
MAX_Q = SCRIPT.get("max_questions", 10)


@pytest.fixture
def client():
    """FastAPI TestClient"""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def rm():
    """RoomManager 实例（重置用）"""
    return room_manager


@pytest.fixture
def fresh_room(rm):
    """创建一个独立的房间，避免用例互相影响（提问上限与生产一致）"""
    room = rm.create_room("tester", max_questions=MAX_Q)
    game_engine.start_game(room)
    return room


@pytest.fixture
def judge():
    return question_judge


@pytest.fixture
def engine():
    return game_engine


@pytest.fixture
def deck():
    return deck_engine

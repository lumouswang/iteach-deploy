"""汤探局 - 受限提问判定器"""
from typing import Dict, Any, Optional


class QuestionJudge:
    """根据预设 JSON 判定提问"""

    def __init__(self, questions_data: Dict[str, Any]):
        self._by_id: Dict[str, Dict[str, Any]] = {
            q["id"]: q for q in questions_data.get("questions", [])
        }

    def list_questions(self, public_only: bool = True) -> list:
        """返回 20 题列表（public_only 隐藏答案/提示，仅给前端展示）"""
        qs = []
        for q in self._by_id.values():
            if public_only:
                qs.append({
                    "id": q["id"],
                    "category": q["category"],
                    "text": q["text"],
                    "knowledge_point": q.get("knowledge_point", ""),
                })
            else:
                qs.append(q)
        return qs

    def judge(self, qid: str) -> Optional[Dict[str, Any]]:
        """根据 qid 查表，返回完整判定"""
        q = self._by_id.get(qid)
        if not q:
            return None
        return {
            "qid": q["id"],
            "category": q["category"],
            "text": q["text"],
            "answer": q["answer"],
            "hint": q["hint"],
            "suggested_card": q.get("suggested_card", ""),
            "knowledge_point": q.get("knowledge_point", ""),
        }

    def is_negation(self, answer: str) -> bool:
        return answer == "否"

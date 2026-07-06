from datetime import datetime

from database.models import MemoryCandidateRecord, SessionLocal


CANDIDATE_STATUS_SAVED = "saved"
CANDIDATE_STATUS_REJECTED = "rejected"
CANDIDATE_STATUS_POSTPONED = "postponed"


def save_memory_candidate_record(candidate, status, saved_memory_id=None):
    """Memory Candidateの提案結果（保存/保存しない/後で確認）を、監査用の専用テーブルへ記録します。

    これは実際の長期記憶（memoriesテーブル）とは別の記録であり、
    「どんな候補が提案され、ユーザーがどう判断したか」の履歴を残すためのものです。
    保存された場合は saved_memory_id で memories テーブルのレコードと紐付けます。
    """
    candidate = candidate or {}

    db = SessionLocal()

    record = MemoryCandidateRecord(
        created_at=datetime.now().isoformat(),
        source_tool=candidate.get("source_tool"),
        source_url=candidate.get("source_url"),
        title=candidate.get("title"),
        summary=candidate.get("summary"),
        candidate_type=candidate.get("candidate_type"),
        risk_level=candidate.get("risk_level"),
        status=status,
        saved_memory_id=saved_memory_id,
    )

    db.add(record)
    db.commit()

    db.close()


def get_recent_memory_candidate_records(limit=20):
    """直近のMemory Candidate提案履歴を、新しい順に取得します。"""
    db = SessionLocal()

    records = (
        db.query(MemoryCandidateRecord)
        .order_by(MemoryCandidateRecord.id.desc())
        .limit(limit)
        .all()
    )

    db.close()

    records.reverse()

    return records

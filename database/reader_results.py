from datetime import datetime

from database.models import ReaderResult, SessionLocal


def save_reader_result(source_tool, title, location, text, truncated=False):
    """Reader（Web/File/PDF/Word/Excel/PowerPoint/YouTube/Image）が読み取った本文全文を保存します。

    これは生ログ（Raw Log相当）の保存であり、長期記憶そのものではありません。
    将来長期記憶へ昇格させる際は、全文をそのまま使わず必要な情報に絞って
    要約・抽出する設計にします（docs/reader_memory_policy.md参照）。
    """
    db = SessionLocal()

    record = ReaderResult(
        created_at=datetime.now().isoformat(),
        source_tool=source_tool,
        title=title,
        location=location,
        text=text,
        truncated=bool(truncated),
    )

    db.add(record)
    db.commit()

    db.close()


def get_recent_reader_results(limit=20):
    """直近保存されたReader結果全文を、新しい順に取得します。"""
    db = SessionLocal()

    results = (
        db.query(ReaderResult)
        .order_by(ReaderResult.id.desc())
        .limit(limit)
        .all()
    )

    db.close()

    results.reverse()

    return results

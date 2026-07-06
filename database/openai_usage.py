from datetime import datetime

from database.models import OpenAIUsageLog, SessionLocal


def record_openai_usage(feature, model, estimated_cost_usd):
    """OpenAI呼び出しの想定利用額を記録します。

    ここに記録するのはPersonalAI側の概算値であり、OpenAI側の実際の請求額とは
    異なる場合があります（安全側に倒した概算のため、実際の請求額はこれ以下になる想定です）。
    """
    db = SessionLocal()

    record = OpenAIUsageLog(
        created_at=datetime.now().isoformat(),
        feature=feature,
        model=model,
        estimated_cost_usd=estimated_cost_usd,
    )

    db.add(record)
    db.commit()

    db.close()


def get_monthly_openai_usage_total(year_month=None):
    """当月（または指定した年月, 'YYYY-MM'形式）の想定利用額合計を返します。"""
    if year_month is None:
        year_month = datetime.now().strftime("%Y-%m")

    db = SessionLocal()

    try:
        records = (
            db.query(OpenAIUsageLog)
            .filter(OpenAIUsageLog.created_at.like(f"{year_month}%"))
            .all()
        )

        return sum(record.estimated_cost_usd or 0.0 for record in records)
    finally:
        db.close()

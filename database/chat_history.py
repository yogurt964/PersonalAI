from datetime import datetime

from database.models import SessionLocal
from database.models import Conversation


def save_message(role, content):

    db = SessionLocal()

    message = Conversation(
        created_at=datetime.now().isoformat(),
        role=role,
        content=content
    )

    db.add(message)
    db.commit()

    db.close()


def get_messages():

    db = SessionLocal()

    messages = db.query(Conversation).all()

    db.close()

    return messages

def get_recent_messages(limit=20):

    db = SessionLocal()

    messages = (
        db.query(Conversation)
        .order_by(Conversation.id.desc())
        .limit(limit)
        .all()
    )

    db.close()

    messages.reverse()

    return messages
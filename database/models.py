from sqlalchemy import create_engine
from sqlalchemy import Boolean, Column, Integer, String, Text
from sqlalchemy import text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///data/personal_ai.db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(String)
    role = Column(String)
    content = Column(Text)


class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(String)
    updated_at = Column(String)
    content = Column(Text)
    memory_type = Column(String)
    category = Column(String)
    memory_key = Column(String)
    subcategory = Column(String)
    scope = Column(String, default="global")
    confidence = Column(Integer, default=80)
    expires_at = Column(String)
    is_active = Column(Boolean, default=True)
    importance = Column(Integer)
    source = Column(String)
    tags = Column(String)


def create_database():
    Base.metadata.create_all(bind=engine)
    migrate_memories_table()


def migrate_memories_table():
    """既存のmemoriesテーブルに、Ver0.13で必要な列を安全に追加します。"""
    # create_allは既存テーブルの列追加までは行わないため、
    # SQLiteのALTER TABLEで足りない列だけを追加します。
    required_columns = {
        "updated_at": "updated_at DATETIME NULL",
        "memory_key": "memory_key TEXT NULL",
        "subcategory": "subcategory TEXT NULL",
        "scope": "scope TEXT DEFAULT 'global'",
        "confidence": "confidence INTEGER DEFAULT 80",
        "expires_at": "expires_at DATETIME NULL",
        "is_active": "is_active BOOLEAN DEFAULT 1",
    }

    with engine.begin() as connection:
        existing_columns = {
            row[1]
            for row in connection.execute(text("PRAGMA table_info(memories)")).fetchall()
        }

        for column_name, column_sql in required_columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    text(f"ALTER TABLE memories ADD COLUMN {column_sql}")
                )

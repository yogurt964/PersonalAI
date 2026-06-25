from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Text
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
    content = Column(Text)
    memory_type = Column(String)
    category = Column(String)
    importance = Column(Integer)
    source = Column(String)
    tags = Column(String)


def create_database():
    Base.metadata.create_all(bind=engine)
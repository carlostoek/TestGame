from sqlmodel import SQLModel, Field, create_engine, Session, select
from typing import Optional
from datetime import datetime

engine = create_engine('sqlite:///database.db')

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    points: int = 0
    level: int = 1
    badges: str = ''  # comma separated badges

class Mission(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id")
    description: str
    points: int
    expires_at: Optional[datetime] = None

# create tables
SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)

def get_or_create_user(user_id: int) -> User:
    with get_session() as session:
        statement = select(User).where(User.id == user_id)
        user = session.exec(statement).first()
        if not user:
            user = User(id=user_id)
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

def reset_missions(user_id: int):
    with get_session() as session:
        statement = select(Mission).where(Mission.user_id == user_id)
        missions = session.exec(statement).all()
        for m in missions:
            session.delete(m)
        session.commit()

from typing import List

from sqlalchemy.orm import Session

from user import model, schema


async def get_user_by_username(db: Session, username: str) -> List[model.User]:
    return db.query(model.User).filter(model.User.username == username).all()


async def get_user_by_id(db: Session, user_id: int) -> model.User:
    return db.query(model.User).filter(model.User.id == user_id).first()


async def save_user(db: Session, user: schema.UserCreate) -> None:
    db_user = model.User(username=user.username, email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

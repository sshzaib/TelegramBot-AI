from .models import Base, User, Conversation
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

engine = create_engine("sqlite:///db.sqlite3", echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)


def get_db():
    db = db_session()
    try:
        yield db
    finally:
        next(get_db)

def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()

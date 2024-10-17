from database.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

database_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "db.sqlite3") #save at the root file db.sqlite3


engine = create_engine(f"sqlite:///{database_path}", echo=True)  #manage database connection
Session = sessionmaker(bind=engine) #to work with database provide methods to work with database
db_session = Session()


def get_db():
    db_session = Session()
    try:
        yield db_session
    finally:
        db_session.close()


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable= False)
    firstname = Column(String)
    lastname = Column(String)

    conversations = relationship("Conversation", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversation"
    id = Column(Integer, primary_key=True)
    text = Column(String)
    imageurl = Column(String)
    response = Column(String)

    user_id = Column(Integer, ForeignKey("user.id"))

    user = relationship("User", back_populates="conversations")

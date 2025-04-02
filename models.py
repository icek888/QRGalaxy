from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)  # позже захэшируем
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    qrcodes = relationship("QRCodeEntry", back_populates="user")

class QRCodeEntry(Base):
    __tablename__ = 'qr_codes'

    id = Column(Integer, primary_key=True)
    url = Column(String)
    filename = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user = relationship("User", back_populates="qrcodes")


# Выбор SQLite — позже можно заменить на PostgreSQL
engine = create_engine('sqlite:///qr_app.db', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

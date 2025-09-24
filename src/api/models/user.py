from sqlalchemy import Column, Integer, String, Boolean

from models import Base
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    scenarios = relationship('Scenario', back_populates='owner')
    is_admin = Column(Boolean, default=False)
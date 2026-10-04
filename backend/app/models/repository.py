from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)

    scans = relationship("Scan", back_populates="repository",
                         cascade="all, delete-orphan")
    # ADD THIS LINE:
    files = relationship("File", back_populates="repository",
                         cascade="all, delete-orphan")

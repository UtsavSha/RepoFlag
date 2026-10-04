from sqlalchemy import Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from .base import Base


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey(
        "repositories.id", ondelete="CASCADE"))
    file_path = Column(String, nullable=False, index=True)

    # Intelligence Metrics (Populated by git_history.py and complexity.py)
    commit_count = Column(Integer, default=0)
    author_count = Column(Integer, default=0)
    complexity_score = Column(Float, default=0.0)

    # The file's individual risk score (Populated by risk_engine/file_risk.py)
    file_risk_score = Column(Float, default=0.0)

    repository = relationship("Repository", back_populates="files")
    findings = relationship(
        "Finding", back_populates="file", cascade="all, delete-orphan")

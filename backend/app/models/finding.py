from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id", ondelete="CASCADE"))
    # ADD THIS LINE to link the finding to a specific file in the database
    file_id = Column(Integer, ForeignKey(
        "files.id", ondelete="CASCADE"), nullable=True)

    scanner_name = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Keep as fallback/reference
    line_number = Column(Integer, nullable=True)
    description = Column(String, nullable=False)

    scan = relationship("Scan", back_populates="findings")
    # ADD THIS LINE:
    file = relationship("File", back_populates="findings")

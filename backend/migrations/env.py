from app.models.repository import Repository
from app.models.scan import Scan
from app.models.file import File
from app.models.finding import Finding
from app.models.base import Base
from alembic import context
from sqlalchemy import pool
from sqlalchemy import engine_from_config
from logging.config import fileConfig
import sys
import os
# Add your backend folder to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# IMPORT YOUR BASE AND ALL MODELS HERE

# Tell Alembic to use your models for auto-generating migrations
target_metadata = Base.metadata

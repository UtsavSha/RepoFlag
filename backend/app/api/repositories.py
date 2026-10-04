from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models import Repository

router = APIRouter(prefix="/api/repositories", tags=["Repositories"])


@router.post("/")
def create_repository(url: str, name: str, owner: str, db: Session = Depends(get_db)):
    # Check if repo already exists
    existing_repo = db.query(Repository).filter(Repository.url == url).first()
    if existing_repo:
        raise HTTPException(
            status_code=400, detail="Repository already registered")

    repo = Repository(url=url, name=name, owner=owner)
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


@router.get("/")
def get_all_repositories(db: Session = Depends(get_db)):
    return db.query(Repository).all()


@router.get("/{repo_id}")
def get_repository(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo

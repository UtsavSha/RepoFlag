from fastapi import FastAPI
from .core.database import engine
from .models.base import Base
from .api import repositories, scans, assistant

# Import the routers we just created
from .api import repositories, scans
from dotenv import load_dotenv
load_dotenv()

# Ensure tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Repoflag API")

# Register the modular routes
app.include_router(repositories.router)
app.include_router(scans.router)
app.include_router(assistant.router)


@app.get("/")
def health_check():
    return {"status": "Repoflag Backend is running, modular routes are active!"}

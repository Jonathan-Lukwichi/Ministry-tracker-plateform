from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asqlite
import os

app = FastAPI()

# Database path is relative to the `backend` directory
DB_PATH = os.path.join("..", "ministry_video_fetcher", "ministry_videos.db")


# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, adjust for production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
def read_root():
    return {"message": "Ministry Analytics Backend"}


import logging

logging.basicConfig(level=logging.INFO)

@app.get("/api/sermons")
async def get_sermons():
    """
    API endpoint to fetch all sermon videos from the database.
    """
    logging.info("get_sermons called")
    try:
        async with asqlite.connect(DB_PATH) as db:
            db.row_factory = asqlite.Row
            async with db.cursor() as cursor:
                await cursor.execute("SELECT * FROM videos ORDER BY upload_date DESC")
                rows = await cursor.fetchall()
                # Convert rows to a list of dictionaries for JSON serialization
                sermons = [dict(row) for row in rows]
                logging.info(f"Found {len(sermons)} sermons")
                return sermons
    except Exception as e:
        logging.error(f"Error in get_sermons: {e}")
        return {"error": str(e)}

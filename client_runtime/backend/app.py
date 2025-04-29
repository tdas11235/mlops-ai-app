from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncpg
import os
from datetime import datetime, time, timezone
import pytz
import logging
import logger_config
from prometheus_client import Counter, Histogram, start_http_server
import threading
import time as t


logger_config.set_logger()
logger = logging.getLogger("backend")
IST = pytz.timezone("Asia/Kolkata")

app = FastAPI()

# Database config
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")


# Prometheus metrics
REQUEST_COUNT = Counter("api_requests_total",
                        "Total number of API requests", ["endpoint"])
REQUEST_LATENCY = Histogram("api_request_latency_seconds",
                            "Latency of API requests in seconds", ["endpoint"])
REQUEST_ERRORS = Counter("api_request_errors_total",
                         "Total number of errors", ["endpoint"])


def start_prometheus_server():
    start_http_server(9000)
threading.Thread(target=start_prometheus_server, daemon=True).start()


# Models
class Article(BaseModel):
    id: int
    title: str
    publication_timestamp: datetime
    article_link: str
    summary: Optional[str]
    image_base64: Optional[str]
    sentiment: Optional[int]

class Feedback(BaseModel):
    article_id: int
    corrected_sentiment: int


# Database connection
async def connect_db():
    return await asyncpg.connect(
        host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD, port=DB_PORT
    )


@app.get("/articles", response_model=List[Article])
async def get_articles(start_date: str, end_date: str, sentiment: Optional[int] = None):
    endpoint = "/articles"
    REQUEST_COUNT.labels(endpoint=endpoint).inc()
    start_time = t.time()
    try:
        conn = await connect_db()
        logger.info("Connected to database!")

        # Parse dates
        start_datetime = IST.localize(datetime.combine(
            datetime.strptime(start_date, "%Y-%m-%d"), time(0, 0, 0)))
        end_datetime = IST.localize(datetime.combine(
            datetime.strptime(end_date, "%Y-%m-%d"), time(23, 59, 59)))

        # Build query
        query = """
            SELECT a.id, a.title, a.publication_timestamp, 
                a.article_link, a.summary, i.image_base64,
                a.sentiment
            FROM articles a
            LEFT JOIN images i ON a.id = i.article_id
            WHERE a.publication_timestamp BETWEEN $1 AND $2
        """

        params = [start_datetime, end_datetime]

        if sentiment is not None:
            query += " AND a.sentiment = $3"
            params.append(sentiment)

        query += " ORDER BY a.publication_timestamp DESC"

        rows = await conn.fetch(query, *params)
        await conn.close()

        articles = []
        for record in rows:
            ist_time = record["publication_timestamp"].replace(
                tzinfo=pytz.utc).astimezone(IST)
            articles.append(Article(
                id=record["id"],
                title=record["title"],
                publication_timestamp=ist_time,
                article_link=record["article_link"],
                summary=record["summary"],
                image_base64=record["image_base64"],
                sentiment=record["sentiment"]
            ))

        logger.info(f"Fetched {len(articles)} articles!")
        return articles
    except Exception as e:
        REQUEST_ERRORS.labels(endpoint=endpoint).inc()
        raise e
    finally:
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(
            t.time() - start_time)


@app.post("/feedback")
async def post_feedback(feedback: Feedback):
    endpoint = "/feedback"
    REQUEST_COUNT.labels(endpoint=endpoint).inc()
    start_time = t.time()
    try:
        logger.info(f"Received feedback: {feedback}")
        conn = await connect_db()
        # Fetch title from database
        title_query = "SELECT title FROM articles WHERE id = $1"
        row = await conn.fetchrow(title_query, feedback.article_id)
        await conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        article_title = row['title'].replace(",", " ")
        feedback_line = f"{feedback.article_id},{feedback.corrected_sentiment},\"{article_title}\",{datetime.now(timezone.utc).isoformat()}\n"

        feedback_dir = "/data"
        os.makedirs(feedback_dir, exist_ok=True)
        feedback_file = os.path.join(feedback_dir, "feedback.csv")
        with open(feedback_file, "a") as f:
            f.write(feedback_line)

        logger.info(f"Feedback recorded for article ID {feedback.article_id}")
        return {"message": "Feedback recorded"}
    except Exception as e:
        REQUEST_ERRORS.labels(endpoint=endpoint).inc()
        raise e
    finally:
        REQUEST_LATENCY.labels(endpoint=endpoint).observe(
            t.time() - start_time)

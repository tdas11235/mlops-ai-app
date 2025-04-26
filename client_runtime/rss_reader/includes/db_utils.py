import psycopg2
import os
import datetime as dt
from psycopg2.extras import Json
import logging


logger = logging.getLogger("db_utils")

DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")


def push(data_list):
    """Function to push rss feed to database"""
    if not data_list:
        logger.warning("Empty list!")
        return
    try:
        new_items = 0
        conn = psycopg2.connect(
            database=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
        )
        cursor = conn.cursor()
        for data in data_list:
            insert_article = """
            INSERT INTO articles (title, publication_timestamp, article_link, summary, sentiment, tags)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (title, publication_timestamp) DO NOTHING
            RETURNING id;
            """
            cursor.execute(
                insert_article, (data["title"], data["pub_time"], data["link"], data["summary"], data["sentiment"], Json(data["tags"])))
            article_id = cursor.fetchone()
            if article_id:
                new_items += 1
            if data["img_b64"] and article_id:
                insert_image = """
                INSERT INTO images (article_id, image_base64)
                VALUES (%s, %s);
                """
                cursor.execute(insert_image, (article_id[0], data["img_b64"]))
        conn.commit()
        logger.info(f"Inserted {new_items} articles successfully.")

    except Exception as e:
        logger.error(f"Error inserting data: {e}")

    finally:
        # closing connections to prevent locks or connection leaks regardless of status
        cursor.close()
        conn.close()

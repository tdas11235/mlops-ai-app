import feedparser as fr
import time
import datetime as dt
import includes.image_utils as iu
import os
import pytz
import logging
import json
import requests


logger = logging.getLogger("fetcher")

IST = pytz.timezone("Asia/Kolkata")
RSS_FEED_URL = os.getenv("RSS_FEED_URL")

batch_size = 16
model_api = "http://mlflow-model:5001/invocations"
headers = {'Content-Type': 'application/json'}


def rss_parser(rss_entry):
    """Function to parse rss feed"""
    title = rss_entry.get('title', '').strip()
    if not title:
        logger.error("Title cannot be blank")
        raise ValueError("Title cannot be blank")
    date_str = rss_entry.get('published', '').strip()
    if date_str:
        date_obj = dt.datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
        date_obj = date_obj.astimezone(IST)
        date_obj = date_obj.strftime("%Y-%m-%d %H:%M:%S%z")
    else:
        date_obj = None
    article_link = rss_entry.get('link', '').strip()
    if not article_link:
        logger.error("Article link cannot be blank")
        raise ValueError("Article link cannot be blank")
    image_url = None
    if 'media_content' in rss_entry and rss_entry['media_content']:
        for media in rss_entry['media_content']:
            if media.get('medium') == 'image':
                image_url = media.get('url')
                break
    image_path = None
    image_base64 = ''
    if image_url:
        filename = image_url.split("/")[-1]
        image_path = iu.download_image(image_url, filename)
        if image_path:
            image_base64 = iu.image_to_base64(image_path)
            os.remove(image_path)
    tags = [tag['term'] for tag in rss_entry.get('tags', [])]
    summary = rss_entry.get('summary', '').strip()
    data = {
        "title": title,
        "pub_time": date_obj,
        "link": article_link,
        "img_b64": image_base64,
        "tags": tags,
        "summary": summary
    }
    return data


def fetch_rss():
    """Function to fetch rss feed from api endpoint"""
    logger.info("Fetching RSS feed...")
    feed = fr.parse(RSS_FEED_URL)
    data_list = []
    for entry in feed.entries:
        data_list.append(rss_parser(entry))
    logging.info("Proceeding to sentiment analysis...")
    all_texts = [item["title"] for item in data_list]
    for i in range(0, len(all_texts), batch_size):
        batch_texts = all_texts[i:i+batch_size]
        payload = {
            "instances": [
                {"text": batch_texts}
            ]
        }
        try:
            response = requests.post(
                model_api, data=json.dumps(payload), headers=headers)
            response.raise_for_status()
            preds = response.json()['predictions']
            # Update the corresponding data_list entries
            for j, pred in enumerate(preds):
                data_list[i + j]['sentiment'] = pred
        except Exception as e:
            logger.error(f"Failed batch {i//batch_size + 1}: {e}")

    logging.info(f"Returning {len(data_list)} news items.")
    return data_list

FROM python:3.10

WORKDIR /app

COPY . . 

RUN apt-get update && apt-get install -y netcat-traditional 

RUN chmod +x /app/waiter.sh

ENV PYTHONPATH="/app/includes"

RUN pip install psycopg2-binary requests feedparser pytz apscheduler requests

CMD ["/app/waiter.sh", "db", "5432", "python", "/app/rss_reader.py"]
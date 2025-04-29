FROM python:3.10

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y netcat-traditional 

RUN chmod +x /app/waiter.sh

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 9500 9000

CMD ["/app/waiter.sh", "db", "5432", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "9500"]
DO
$$
BEGIN
   IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'mlops_app') THEN
      CREATE DATABASE mlops_a4;
   END IF;
END
$$;

\c mlops_app;

ALTER DATABASE mlops_app SET TIME ZONE 'Asia/Kolkata';
SET TIME ZONE 'Asia/Kolkata';
SHOW TIME ZONE;

CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    publication_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    article_link TEXT NOT NULL,
    summary TEXT,
    sentiment VARCHAR(20),
    tags JSONB,
    CONSTRAINT unique_title_pubtime UNIQUE (title, publication_timestamp)
);

CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    image_base64 TEXT NOT NULL
);
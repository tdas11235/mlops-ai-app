CREATE_FEEDBACK_TABLE = """
CREATE TABLE IF NOT EXISTS article_feedback (
    id SERIAL PRIMARY KEY,
    article_title TEXT NOT NULL,
    sentiment TEXT,
    feedback_time TIMESTAMP NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    UNIQUE (article_title, feedback_time)
);
"""

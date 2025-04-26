import streamlit as st
import requests
from datetime import date

API_URL = "http://backend:9500"

st.set_page_config(page_title="News Sentiment", layout="wide")
st.title("News Sentiment Dashboard")

st.sidebar.header("Filters")
start_date = st.sidebar.date_input("Start Date", date.today())
end_date = st.sidebar.date_input("End Date", date.today())

sentiment_map = {"All": None, "Negative": 0, "Neutral": 1, "Positive": 2}
sentiment_choice = st.sidebar.selectbox(
    "Sentiment", list(sentiment_map.keys()))

params = {
    "start_date": start_date.isoformat(),
    "end_date": end_date.isoformat()
}

if sentiment_map[sentiment_choice] is not None:
    params["sentiment"] = sentiment_map[sentiment_choice]


# Fetch articles
try:
    response = requests.get(f"{API_URL}/articles", params=params)
    response.raise_for_status()
    articles = response.json()

    if not articles:
        st.info("No articles found for the selected filters.")
    else:
        st.write(f"Showing {len(articles)} articles")
        for article in articles:
            with st.expander(article['title']):
                st.write(
                    f"**Published on:** {article['publication_timestamp']}")
                st.write(article['summary'])
                st.markdown(f"[Read full article]({article['article_link']})")
                if article['image_base64']:
                    st.image(
                        f"data:image/jpeg;base64,{article['image_base64']}", use_container_width=True)

                new_sentiment = st.radio(
                    f"Correct sentiment for article {article['id']}",
                    options=["Negative", "Neutral", "Positive"],
                    horizontal=True,
                    index=article['sentiment']
                )

                if st.button(f"Submit Feedback {article['id']}"):
                    feedback_payload = {
                        "article_id": article['id'],
                        "corrected_sentiment": sentiment_map[new_sentiment]
                    }
                    feedback_response = requests.post(
                        f"{API_URL}/feedback", json=feedback_payload)
                    if feedback_response.ok:
                        st.success("Feedback submitted!")
                    else:
                        st.error("Failed to submit feedback.")

except Exception as e:
    st.error(f"Error fetching articles: {e}")

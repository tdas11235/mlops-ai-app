import streamlit as st
import requests
from datetime import date
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import time
from streamlit_autorefresh import st_autorefresh


API_URL = "http://backend:9500"


user_manual = """
# 📰 News Sentiment Dashboard - User Manual

1. 📅 **Date Filters**  
   - 🕒 Use the **Start Date** and **End Date** selectors in the sidebar to choose the date range for news articles.  
   - ⏰ Start Date sets the time to **00:00 hrs IST** of the selected date.  
   - ⌛ End Date sets the time to **23:59 hrs IST** of the selected date.  

2. 🎯 **Sentiment Filter**  
   - 🎭 Filter news by sentiment:  
     - **All**: Get all articles within the selected date range.  
     - 😠 **Negative**, 😐 **Neutral**, 😊 **Positive** 

3. 👁️ **View Modes**  
   - 🗞️ **Articles**:  
     - Each article appears as a **headline inside an expander**.  
     - Click the expander to view:  
       - 🗓️ Publishing date  
       - 🔗 Link to full article  
       - 🖼️ Image (if available)  
       - 🧠 Sentiment is shown as a **highlighted radio button**  
   - ☁️ **WordCloud**:  
     - Visual representation of keywords from article summaries.  
     - Color-coded by sentiment selected.  

4. 🛠️ **Feedback**  
   - 🧩 Adjust the sentiment classification if needed.  
   - 👍 Just select the correct sentiment and click **Submit Feedback**.  
   - 📊 Your feedback helps us **improve the model** continuously.  

5. 🔄 **Auto-Refresh**  
   - ⏱️ The dashboard auto-refreshes **every 10 minutes**  
   - 🆕 Ensures you're always seeing fresh, up-to-date news.
"""


st.set_page_config(page_title="News Sentiment", layout="wide")
st_autorefresh(interval=600000, limit=None, key="autorefresh")
st.title("News Sentiment Dashboard")

with st.expander("📘 How to Use This Dashboard"):
    st.markdown(user_manual.replace('\n', '  \n'))  # Markdown line breaks

st.sidebar.header("Filters")
start_date = st.sidebar.date_input("Start Date", date.today())
end_date = st.sidebar.date_input("End Date", date.today())

sentiment_map = {"All": None, "Negative": 0, "Neutral": 1, "Positive": 2}
sentiment_choice = st.sidebar.selectbox(
    "Sentiment", list(sentiment_map.keys()))

view_choice = st.sidebar.radio(
    "View", ["Articles", "WordCloud"]
)

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
        if view_choice == "WordCloud":
            # --- WordCloud view ---
            all_text = " ".join(
                f"{(article.get('title', '') + ' ')} {article.get('summary', '')}"
                for article in articles
                if article.get('summary') or article.get('title')
            )
            if all_text:
                if sentiment_choice == "Positive":
                    colormap = "Greens"
                elif sentiment_choice == "Negative":
                    colormap = "Reds"
                elif sentiment_choice == "Neutral":
                    colormap = "Greys"
                else:
                    colormap = "Blues"  # Default for "All"

                wordcloud = WordCloud(
                    width=800,
                    height=400,
                    background_color='white',
                    colormap=colormap
                ).generate(all_text)

                st.subheader("WordCloud of Article Summaries")
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
            else:
                st.info("No summaries available to generate WordCloud.")

        else:
            # --- Articles view ---
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

import streamlit as st
from pymongo import MongoClient
import pandas as pd
import plotly.express as px

#PLAN:
#Chart 1 (MongoDB): Average rating over time
#Chart 2 (MySQL): Average revenue over time

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["tmdb_movies"]
collection = db["movies"]

st.title("TMDB Movies Dashboard")
st.write("Exploring how the film industry has changed over time. " \
"This dashboard uses data from TMDB, stored in MongoDB and MySQL, to visualize trends in movie ratings and revenue over the years." \
" We will be focusing on two of our analytical questions: How has the film industry changed over time? ")

# Load data from MongoDB
df = pd.DataFrame(list(collection.find({}, {"_id": 0, "release_date": 1, "vote_average": 1, "revenue": 1})))
df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
df["year"] = df["release_date"].dt.year
df = df.dropna(subset=["year"])
df["year"] = df["year"].astype(int)

# Filter to reasonable year range
df = df[(df["year"] >= 1950) & (df["year"] <= 2024)]

# Interactive filter - year range slider
st.subheader("Filter by Year Range")
min_year = int(df["year"].min())
max_year = int(df["year"].max())

year_range = st.slider(
    "Select year range:",
    min_value=min_year,
    max_value=max_year,
    value=(1980, 2024)
)

df_filtered = df[(df["year"] >= year_range[0]) & (df["year"] <= year_range[1])]

# Chart 1
st.subheader("Average Movie Rating Over Time")
rating_by_year = df_filtered.groupby("year")["vote_average"].mean().reset_index()
fig1 = px.line(rating_by_year, x="year", y="vote_average", title="Average Rating by Year")
st.plotly_chart(fig1)
st.write("This chart shows the average movie rating over time. You can use the slider above to filter the data by year range and see how ratings have changed over different periods.")

#Need to load in data from MYSQL for the second chart, but since I don't have that set up yet, I'll just create a placeholder chart for now.
st.subheader("Average Movie Revenue Over Time")
st.write("Placeholder for MySQL chart")
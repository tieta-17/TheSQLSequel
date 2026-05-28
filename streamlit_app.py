import streamlit as st
import pandas as pd
from pymongo import MongoClient
import plotly.express as px

# -----------------------------
# CONFIG & STYLES
# -----------------------------
st.set_page_config(
    page_title="TMDB Movies Analytics Dashboard",
    page_icon="🎬",
    layout="wide"
)

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "tmdb_movies"

# -----------------------------
# ROBUST DATABASE LOADER
# -----------------------------
@st.cache_data(ttl=600)
def load_data_from_mongodb(collection_name):
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        collection = db[collection_name]
        
        raw_documents = list(collection.find())
        client.close()
        
        if not raw_documents:
            return pd.DataFrame()
            
        cleaned_rows = []
        for doc in raw_documents:
            row = doc.copy()
            
            # Case A: If _id is a nested compound dictionary (Tab 3: Country & Genre)
            if isinstance(row.get("_id"), dict):
                for sub_key, sub_val in row["_id"].items():
                    row[sub_key] = sub_val
            
            # Case B: If _id is a primitive value (Tab 1: Budget, Tab 2: Genre, Tab 4: Year)
            elif "_id" in row and row["_id"] is not None:
                row["extracted_id_key"] = row["_id"]
                
            # Safely pop the BSON _id out so Pandas doesn't use it as an index
            row.pop("_id", None)
            cleaned_rows.append(row)
            
        # Forces a clean DataFrame with plain sequence numbering (0, 1, 2...)
        return pd.DataFrame(cleaned_rows).reset_index(drop=True)
    except Exception as e:
        st.error(f"Database error reading '{collection_name}': {e}")
        return pd.DataFrame()

# -----------------------------
# APP HEADER
# -----------------------------
st.title("🎬 TMDB Movie Insights Dashboard")
st.markdown("An interactive analysis powered by MongoDB aggregate pipelines.")
st.divider()

# Fetching Data
with st.spinner("Fetching data..."):
    df_budget_success = load_data_from_mongodb("query1_budget_success")
    df_genre_economics = load_data_from_mongodb("query2_genre_economics")
    df_country_genres = load_data_from_mongodb("query3_country_genres")
    df_yearly_trends = load_data_from_mongodb("query4_yearly_trends")

tab1, tab2, tab3, tab4 = st.tabs([
    "💰 Budget vs Success", 
    "🎭 Genre Economics", 
    "🌍 Country & Genre Popularity", 
    "📈 Historical Trends"
])

# ==========================================
# TAB 1: BUDGET VS SUCCESS
# ==========================================
with tab1:
    st.header("Financial Performance by Budget Class Tier")
    if not df_budget_success.empty and "extracted_id_key" in df_budget_success.columns:
        df_budget_success = df_budget_success.rename(columns={"extracted_id_key": "Budget Range"})
        
        # 1. Clean up the MongoDB bucket keys so they match our mapping dictionary
        def clean_bucket_id(val):
            try:
                return int(float(val))
            except:
                return str(val)
        df_budget_success["bucket_id"] = df_budget_success["Budget Range"].apply(clean_bucket_id)
        
        # 2. Map the raw starting numbers to beautiful, clean text categories
        bucket_labels = {
            0: "Under $1M",
            1000000: "$1M - $10M",
            10000000: "$10M - $50M",
            50000000: "$50M - $100M",
            100000000: "$100M - $500M",
            "500M+": "$500M+"
        }
        df_budget_success["Budget Category"] = df_budget_success["bucket_id"].map(bucket_labels).fillna(df_budget_success["Budget Range"])
        
        col1, col2 = st.columns([2, 1])
        with col1:
            # 3. Add a toggle so you can test both ways instantly!
            use_log = st.checkbox(
                "Use Logarithmic Scale for Revenue", 
                value=True, 
                help="Turning this off will make small-budget categories look invisible compared to blockbusters."
            )
            
            fig1 = px.bar(
                df_budget_success, 
                x="Budget Category", 
                y="avg_revenue", 
                color="avg_revenue", 
                title="Average Revenue by Budget Category Tier",
                labels={"avg_revenue": "Average Revenue ($)", "Budget Category": "Budget Tier"},
                color_continuous_scale="Viridis",
                # Forces Plotly to keep the categories in order rather than alphabetical sorting
                category_orders={"Budget Category": ["Under $1M", "$1M - $10M", "$10M - $50M", "$50M - $100M", "$100M - $500M", "$500M+"]}
            )
            
            if use_log:
                fig1.update_yaxes(type="log")
                
            st.plotly_chart(fig1, use_container_width=True)
            
        with col2:
            st.subheader("Data Highlights")
            st.dataframe(
                df_budget_success[["Budget Category", "movie_count", "avg_revenue", "avg_rating"]].style.format({
                    "avg_revenue": "${:,.2f}",
                    "avg_rating": "{:.2f}",
                    "movie_count": "{:,}"
                }), 
                hide_index=True, 
                use_container_width=True
            )
    else:
        st.info("No data available for Tab 1.")

# ==========================================
# TAB 2: GENRE ECONOMICS
# ==========================================
with tab2:
    st.header("Genre Economics & Engagement")
    if not df_genre_economics.empty and "extracted_id_key" in df_genre_economics.columns:
        df_genre_economics = df_genre_economics.rename(columns={"extracted_id_key": "Genre"})
        
        sort_metric = st.selectbox("Sort Genres By:", ["avg_revenue", "avg_vote_count", "avg_rating", "movie_count"])
        df_sorted_genres = df_genre_economics.sort_values(by=sort_metric, ascending=False)
        
        fig2 = px.scatter(df_sorted_genres, x="avg_vote_count", y="avg_revenue", size="movie_count", color="Genre", hover_name="Genre")
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(df_sorted_genres[["Genre", "avg_revenue", "avg_vote_count", "avg_rating", "movie_count"]], use_container_width=True, hide_index=True)
    else:
        st.info("No data available for Tab 2.")

# ==========================================
# TAB 3: POPULAR GENRES BY COUNTRY
# ==========================================
with tab3:
    st.header("Global Film Insights: Genre Popularity by Country")
    if not df_country_genres.empty and "country" in df_country_genres.columns and "genre" in df_country_genres.columns:
        all_countries = sorted(df_country_genres["country"].dropna().unique())
        default_idx = all_countries.index("United States of America") if "United States of America" in all_countries else 0
        selected_country = st.selectbox("Select Production Country:", all_countries, index=default_idx)
        
        df_filtered = df_country_genres[df_country_genres["country"] == selected_country].sort_values(by="avg_popularity", ascending=False)
        
        col1, col2 = st.columns(2)
        with col1:
            fig3 = px.bar(df_filtered.head(10), x="avg_popularity", y="genre", orientation="h", title=f"Top Genres in {selected_country}", color="avg_popularity")
            fig3.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig3, use_container_width=True)
        with col2:
            st.dataframe(df_filtered[["genre", "avg_popularity", "avg_vote_count", "movie_count"]], use_container_width=True, hide_index=True)
    else:
        st.info("No data available for Tab 3.")

# ==========================================
# TAB 4: FILM INDUSTRY TRENDS OVER TIME
# ==========================================
with tab4:
    st.header("Historical Film Industry Evolution")
    
    # Check if our extracted key column exists
    if not df_yearly_trends.empty and "extracted_id_key" in df_yearly_trends.columns:
        df_yearly_trends = df_yearly_trends.rename(columns={"extracted_id_key": "Year"})
        
        # Enforce strict translation and remove bad years
        df_yearly_trends["Year"] = pd.to_numeric(df_yearly_trends["Year"], errors='coerce')
        df_yearly_trends = df_yearly_trends.dropna(subset=["Year"])
        df_yearly_trends["Year"] = df_yearly_trends["Year"].astype(int)
        df_yearly_trends = df_yearly_trends[df_yearly_trends["Year"] > 1800].sort_values(by="Year")
        
        if not df_yearly_trends.empty:
            min_y, max_y = int(df_yearly_trends["Year"].min()), int(df_yearly_trends["Year"].max())
            year_range = st.slider("Select Year Range:", min_y, max_y, (max(min_y, 1980), min(max_y, 2024)))
            
            df_filtered = df_yearly_trends[df_yearly_trends["Year"].between(year_range[0], year_range[1])]
            
            if df_filtered.empty:
                st.info("No metrics found in this year window.")
            else:
                kpi1, kpi2 = st.columns(2)
                kpi1.metric("Total Movies in Window", f"{df_filtered['movie_count'].sum():,}")
                
                peak_idx = df_filtered["avg_revenue"].idxmax()
                kpi2.metric("Highest Avg Revenue Year", f"{int(df_filtered.loc[peak_idx, 'Year'])}")
                
                metric_choice = st.radio("View Timeline Variant:", ["Financials", "Audience Ratings"], horizontal=True)
                if metric_choice == "Financials":
                    fig4 = px.line(df_filtered, x="Year", y=["avg_budget", "avg_revenue"])
                else:
                    fig4 = px.line(df_filtered, x="Year", y="avg_popularity")
                st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No valid years could be evaluated from your records.")
    else:
        st.warning("⚠️ Year row ID field missing from the collection. Ensure Step 1's aggregation script ran completely.")
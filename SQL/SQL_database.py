import pandas as pd
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from getpass import getpass


# =========================================================
# DATABASE CONNECTION
# =========================================================

DB_NAME = "movies"

MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": getpass("Enter MySQL Password: ")
}


def create_database():
    """
    Create database if it does not exist.
    """

    conn = pymysql.connect(
        host=MYSQL_CONFIG["host"],
        port=MYSQL_CONFIG["port"],
        user=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"]
    )

    cursor = conn.cursor()

    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"
    )

    conn.commit()

    cursor.close()
    conn.close()

    print(f"Database `{DB_NAME}` is ready.")


def connect_engine():
    """
    Create SQLAlchemy engine.
    """

    url = URL.create(
        drivername="mysql+pymysql",
        username=MYSQL_CONFIG["user"],
        password=MYSQL_CONFIG["password"],
        host=MYSQL_CONFIG["host"],
        port=MYSQL_CONFIG["port"],
        database=DB_NAME,
    )

    engine = create_engine(url)

    return engine


# =========================================================
# CREATE TABLES
# =========================================================

def create_tables(engine):

    with engine.connect() as connection:

        connection.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))

        tables = [
            "production_classification",
            "content_description",
            "financial_metrics",
            "popularity_metrics",
            "general_information"
        ]

        for table in tables:
            connection.execute(
                text(f"DROP TABLE IF EXISTS {table};")
            )

        connection.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))

        # -----------------------------
        # GENERAL INFORMATION
        # -----------------------------

        connection.execute(text("""
            CREATE TABLE general_information (
                movie_id INT PRIMARY KEY,
                title VARCHAR(255),
                original_title VARCHAR(255),
                status VARCHAR(50),
                release_date DATE,
                runtime INT,
                adult BOOLEAN,
                original_language VARCHAR(10)
            );
        """))

        # -----------------------------
        # POPULARITY METRICS
        # -----------------------------

        connection.execute(text("""
            CREATE TABLE popularity_metrics (
                movie_id INT PRIMARY KEY,
                vote_average FLOAT,
                vote_count INT,
                popularity FLOAT,
                FOREIGN KEY (movie_id)
                    REFERENCES general_information(movie_id)
            );
        """))

        # -----------------------------
        # FINANCIAL METRICS
        # -----------------------------

        connection.execute(text("""
            CREATE TABLE financial_metrics (
                movie_id INT PRIMARY KEY,
                budget BIGINT,
                revenue BIGINT,
                FOREIGN KEY (movie_id)
                    REFERENCES general_information(movie_id)
            );
        """))

                # -----------------------------
        # CONTENT DESCRIPTION
        # -----------------------------

        connection.execute(text("""
            CREATE TABLE content_description (
                movie_id INT PRIMARY KEY,
                overview TEXT,
                tagline TEXT,
                keywords TEXT,
                FOREIGN KEY (movie_id)
                    REFERENCES general_information(movie_id)
            );
        """))

        # -----------------------------
        # PRODUCTION CLASSIFICATION
        # -----------------------------

        connection.execute(text("""
            CREATE TABLE production_classification (
                movie_id INT PRIMARY KEY,
                genres TEXT,
                production_companies TEXT,
                production_countries TEXT,
                spoken_languages TEXT,
                FOREIGN KEY (movie_id)
                    REFERENCES general_information(movie_id)
            );
        """))

    print("Tables created successfully.")


# =========================================================
# LOAD CSV DATA
# =========================================================

def load_csv_data(csv_path):

    df = pd.read_csv(csv_path)

    df = df.drop(
        columns=['Unnamed: 0'],
        errors='ignore'
    )

    df['release_date'] = pd.to_datetime(
        df['release_date'],
        errors='coerce'
    ).dt.strftime('%Y-%m-%d')

    df['adult'] = df['adult'].apply(
        lambda x: 1 if x is True else 0
    )

    df = df.where(pd.notnull(df), None)

    print(f"Loaded {len(df)} rows.")

    return df


# =========================================================
# INSERT DATA
# =========================================================

def insert_data(df, engine):

    # -----------------------------
    # GENERAL INFORMATION
    # -----------------------------

    df[
        [
            'movie_id',
            'title',
            'original_title',
            'status',
            'release_date',
            'runtime',
            'adult',
            'original_language'
        ]
    ].to_sql(
        'general_information',
        con=engine,
        if_exists='append',
        index=False
    )

    # -----------------------------
    # POPULARITY METRICS
    # -----------------------------

    df[
        [
            'movie_id',
            'vote_average',
            'vote_count',
            'popularity'
        ]
    ].to_sql(
        'popularity_metrics',
        con=engine,
        if_exists='append',
        index=False
    )

    # -----------------------------
    # FINANCIAL METRICS
    # -----------------------------

    df[
        [
            'movie_id',
            'budget',
            'revenue'
        ]
    ].to_sql(
        'financial_metrics',
        con=engine,
        if_exists='append',
        index=False
    )

    # -----------------------------
    # CONTENT DESCRIPTION
    # -----------------------------

    df[
        [
            'movie_id',
            'overview',
            'tagline',
            'keywords'
        ]
    ].to_sql(
        'content_description',
        con=engine,
        if_exists='append',
        index=False
    )

    # -----------------------------
    # PRODUCTION CLASSIFICATION
    # -----------------------------

    df[
        [
            'movie_id',
            'genres',
            'production_companies',
            'production_countries',
            'spoken_languages'
        ]
    ].to_sql(
        'production_classification',
        con=engine,
        if_exists='append',
        index=False
    )

    print("All data inserted successfully.")


# =========================================================
# QUERY 1
# Budget vs Success
# =========================================================

def get_budget_vs_success(engine):

    query = """
        SELECT
            CASE

                WHEN fm.budget < 1000000
                    THEN '0-1M'

                WHEN fm.budget < 10000000
                    THEN '1M-10M'

                WHEN fm.budget < 50000000
                    THEN '10M-50M'

                WHEN fm.budget < 100000000
                    THEN '50M-100M'

                WHEN fm.budget < 500000000
                    THEN '100M-500M'

                ELSE '500M+'

            END AS budget_range,

            AVG(fm.revenue) AS avg_revenue,
            AVG(pm.vote_average) AS avg_rating,
            AVG(pm.vote_count) AS avg_votes,
            COUNT(*) AS movie_count

        FROM financial_metrics fm

        JOIN popularity_metrics pm
            ON fm.movie_id = pm.movie_id

        WHERE fm.budget > 0
          AND fm.revenue > 0

        GROUP BY budget_range

        ORDER BY avg_revenue ASC;
    """

    return pd.read_sql(query, con=engine)


# =========================================================
# QUERY 2
# Engagement vs Revenue
# =========================================================

def get_engagement_vs_revenue(engine):

    query = """
        SELECT

            pc.genres,

            AVG(pm.vote_count) AS avg_vote_count,
            AVG(fm.revenue) AS avg_revenue,
            AVG(pm.vote_average) AS avg_rating,
            COUNT(*) AS movie_count

        FROM popularity_metrics pm

        JOIN financial_metrics fm
            ON pm.movie_id = fm.movie_id

        JOIN production_classification pc
            ON pc.movie_id = pm.movie_id

        WHERE pm.vote_count > 100
          AND fm.revenue > 0
          AND pc.genres IS NOT NULL

        GROUP BY pc.genres

        ORDER BY avg_revenue DESC;
    """

    return pd.read_sql(query, con=engine)


# =========================================================
# QUERY 3
# Popular Genres by Country
# =========================================================

def get_popular_genres_by_country(engine):

    query = """
        SELECT

            production_countries,
            genres,

            AVG(pm.popularity) AS avg_popularity,
            AVG(pm.vote_count) AS avg_vote_count,
            COUNT(*) AS movie_count

        FROM production_classification pc

        JOIN popularity_metrics pm
            ON pc.movie_id = pm.movie_id

        WHERE production_countries IS NOT NULL
          AND genres IS NOT NULL

        GROUP BY production_countries, genres

        ORDER BY avg_popularity DESC;
    """

    return pd.read_sql(query, con=engine)


# =========================================================
# QUERY 4
# Film Industry Trends Over Time
# =========================================================

def get_film_industry_trends(engine):

    query = """
        SELECT

            YEAR(gi.release_date) AS year,

            AVG(fm.budget) AS avg_budget,
            AVG(fm.revenue) AS avg_revenue,
            AVG(pm.vote_average) AS avg_rating,
            AVG(pm.popularity) AS avg_popularity,
            COUNT(*) AS movie_count

        FROM general_information gi

        JOIN financial_metrics fm
            ON gi.movie_id = fm.movie_id

        JOIN popularity_metrics pm
            ON gi.movie_id = pm.movie_id

        WHERE gi.release_date IS NOT NULL

        GROUP BY year

        ORDER BY year ASC;
    """

    return pd.read_sql(query, con=engine)


# =========================================================
# MAIN
# =========================================================

def main():

    create_database()

    engine = connect_engine()

    create_tables(engine)

    df = load_csv_data(
        "TMDB_cleaned_revenue.csv"
    )

    insert_data(df, engine)

    # Example query usage

    df1 = get_budget_vs_success(engine)
    print(df1.head())

    df2 = get_engagement_vs_revenue(engine)
    print(df2.head())

    df3 = get_popular_genres_by_country(engine)
    print(df3.head())

    df4 = get_film_industry_trends(engine)
    print(df4.head())


if __name__ == "__main__":
    main()
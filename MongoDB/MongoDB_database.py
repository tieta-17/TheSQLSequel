import pandas as pd
from pymongo import MongoClient


# -----------------------------
# DATABASE CONNECTION
# -----------------------------

def connect_to_mongodb(
    uri="mongodb://localhost:27017/",
    db_name="tmdb_movies"
):
    client = MongoClient(uri)
    db = client[db_name]

    return client, db


# -----------------------------
# LOAD DATA INTO MONGODB
# -----------------------------

def load_csv_to_mongodb(
    db,
    csv_path,
    collection_name="movies"
):

    df = pd.read_csv(csv_path)

    # Replace NaN with None
    df = df.where(pd.notnull(df), None)

    movies = df.to_dict(orient="records")

    collection = db[collection_name]

    collection.drop()

    collection.insert_many(movies)

    return collection


# -----------------------------
# QUERY 1
# Budget vs Success
# -----------------------------

def get_budget_vs_success(collection):

    pipeline = [

        {
            "$match": {
                "budget": {"$gt": 0},
                "revenue": {"$gt": 0}
            }
        },

        {
            "$bucket": {
                "groupBy": "$budget",

                "boundaries": [
                    0,
                    1000000,
                    10000000,
                    50000000,
                    100000000,
                    500000000
                ],

                "default": "500M+",

                "output": {

                    "avg_revenue": {
                        "$avg": "$revenue"
                    },

                    "avg_rating": {
                        "$avg": "$vote_average"
                    },

                    "avg_votes": {
                        "$avg": "$vote_count"
                    },

                    "movie_count": {
                        "$sum": 1
                    }
                }
            }
        },

        {
            "$sort": {
                "_id": 1
            }
        }
    ]

    results = list(collection.aggregate(pipeline))

    return pd.DataFrame(results)


# -----------------------------
# QUERY 2
# Engagement vs Revenue by Genre
# -----------------------------

def get_engagement_vs_revenue_by_genre(collection):

    pipeline = [

        {
            "$match": {
                "vote_count": {"$gt": 100},
                "revenue": {"$gt": 0},
                "genres": {"$ne": None}
            }
        },

        {
            "$addFields": {
                "genre_array": {
                    "$split": ["$genres", ", "]
                }
            }
        },

        {
            "$unwind": "$genre_array"
        },

        {
            "$group": {

                "_id": "$genre_array",

                "avg_vote_count": {
                    "$avg": "$vote_count"
                },

                "avg_revenue": {
                    "$avg": "$revenue"
                },

                "avg_rating": {
                    "$avg": "$vote_average"
                },

                "movie_count": {
                    "$sum": 1
                }
            }
        },

        {
            "$sort": {
                "avg_revenue": -1
            }
        }
    ]

    results = list(collection.aggregate(pipeline))

    return pd.DataFrame(results)


# -----------------------------
# QUERY 3
# Popular Genres by Country
# -----------------------------

def get_popular_genres_by_country(collection):

    pipeline = [

        {
            "$match": {
                "production_countries": {"$ne": []}
            }
        },

        {
            "$unwind": "$production_countries"
        },

        {
            "$unwind": "$genres"
        },

        {
            "$group": {

                "_id": {
                    "country": "$production_countries",
                    "genre": "$genres"
                },

                "avg_popularity": {
                    "$avg": "$popularity"
                },

                "avg_vote_count": {
                    "$avg": "$vote_count"
                },

                "movie_count": {
                    "$sum": 1
                }
            }
        },

        {
            "$sort": {
                "avg_popularity": -1
            }
        }
    ]

    results = list(collection.aggregate(pipeline))

    return pd.DataFrame(results)


# -----------------------------
# QUERY 4
# Film Industry Trends Over Time
# -----------------------------

def get_film_industry_trends(collection):

    pipeline = [

        {
            "$match": {
                "release_date": {"$ne": None}
            }
        },

        {
            "$addFields": {
                "year": {
                    "$year": {
                        "$dateFromString": {
                            "dateString": "$release_date"
                        }
                    }
                }
            }
        },

        {
            "$group": {

                "_id": "$year",

                "avg_budget": {
                    "$avg": "$budget"
                },

                "avg_revenue": {
                    "$avg": "$revenue"
                },

                "avg_rating": {
                    "$avg": "$vote_average"
                },

                "avg_popularity": {
                    "$avg": "$popularity"
                },

                "movie_count": {
                    "$sum": 1
                }
            }
        },

        {
            "$sort": {
                "_id": 1
            }
        }
    ]

    results = list(collection.aggregate(pipeline))

    return pd.DataFrame(results)
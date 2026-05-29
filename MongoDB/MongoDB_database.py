import ast
import time
import pandas as pd
from pymongo import MongoClient

# -----------------------------
# CONFIG
# -----------------------------
INPUT_FILE = "TMDB_CLEAN_FINAL.csv"
DB_NAME = "tmdb_movies"


# -----------------------------
# DATABASE CONNECTION
# -----------------------------
def connect_to_mongodb(uri="mongodb://localhost:27017/", db_name=DB_NAME):
    client = MongoClient(uri)
    db = client[db_name]
    return client, db


# -----------------------------
# ROBUST LIST PARSER FOR MONGODB
# -----------------------------
def parse_to_list(value):
    if not isinstance(value, str):
        return []
    try:
        result = ast.literal_eval(value)
        if isinstance(result, list):
            return [str(x).strip() for x in result]
    except (ValueError, SyntaxError):
        pass
    return [x.strip() for x in value.split(",") if x.strip()]


# -----------------------------
# LOAD DATA INTO MONGODB
# -----------------------------
def load_csv_to_mongodb(db, csv_path, collection_name="movies"):
    df = pd.read_csv(csv_path)

    # Replace NaN with None so they translate to MongoDB BSON 'null'
    df = df.where(pd.notnull(df), None)

    # Convert string categories into clean native MongoDB arrays
    df["genres"] = df["genres"].apply(parse_to_list)
    df["production_countries"] = df["production_countries"].apply(parse_to_list)

    collection = db[collection_name]
    collection.drop()  # Clear existing collection data

    movies_dict = df.to_dict("records")
    if movies_dict:
        collection.insert_many(movies_dict)
        print(f"Successfully loaded {len(movies_dict)} source documents into collection: '{collection_name}'")

    return collection


# -----------------------------
# QUERY 1: Budget vs Success
# -----------------------------
def save_budget_vs_success(collection, output_collection_name="query1_budget_success"):
    pipeline = [
        {"$match": {"budget": {"$gt": 0}, "revenue": {"$gt": 0}}},
        {
            "$bucket": {
                "groupBy": "$budget",
                "boundaries": [0, 1000000, 10000000, 50000000, 100000000, 500000000],
                "default": "500M+",
                "output": {
                    "avg_revenue": {"$avg": "$revenue"},
                    "avg_rating": {"$avg": "$vote_average"},
                    "avg_votes": {"$avg": "$vote_count"},
                    "movie_count": {"$sum": 1},
                },
            }
        },
        {"$sort": {"_id": 1}},
        {"$out": output_collection_name}
    ]

    collection.aggregate(pipeline)
    print(f"-> Saved Query 1 results automatically to MongoDB collection: '{output_collection_name}'")


# -----------------------------
# QUERY 2: Engagement vs Revenue by Genre
# -----------------------------
def save_engagement_vs_revenue_by_genre(collection, output_collection_name="query2_genre_economics"):
    pipeline = [
        {
            "$match": {
                "vote_count": {"$gt": 100},
                "revenue": {"$gt": 0},
                "genres": {"$exists": True, "$not": {"$size": 0}},
            }
        },
        {"$unwind": "$genres"},
        {
            "$group": {
                "_id": "$genres",
                "avg_vote_count": {"$avg": "$vote_count"},
                "avg_revenue": {"$avg": "$revenue"},
                "avg_rating": {"$avg": "$vote_average"},
                "movie_count": {"$sum": 1},
            }
        },
        {"$sort": {"avg_revenue": -1}},
        {"$out": output_collection_name}
    ]

    collection.aggregate(pipeline)
    print(f"-> Saved Query 2 results automatically to MongoDB collection: '{output_collection_name}'")


# -----------------------------
# QUERY 3: Popular Genres by Country
# -----------------------------
def save_popular_genres_by_country(collection, output_collection_name="query3_country_genres"):
    pipeline = [
        {
            "$match": {
                "production_countries": {"$exists": True, "$not": {"$size": 0}},
                "genres": {"$exists": True, "$not": {"$size": 0}},
            }
        },
        {"$unwind": "$production_countries"},
        {"$unwind": "$genres"},
        {
            "$group": {
                "_id": {
                    "country": "$production_countries",
                    "genre": "$genres",
                },
                "avg_popularity": {"$avg": "$popularity"},
                "avg_vote_count": {"$avg": "$vote_count"},
                "movie_count": {"$sum": 1},
            }
        },
        {"$sort": {"avg_popularity": -1}},
        {"$out": output_collection_name}
    ]

    collection.aggregate(pipeline)
    print(f"-> Saved Query 3 results automatically to MongoDB collection: '{output_collection_name}'")


# -----------------------------
# QUERY 4: Film Industry Trends Over Time
# -----------------------------
def save_film_industry_trends(collection, output_collection_name="query4_yearly_trends"):
    pipeline = [
        {
            "$match": {
                "release_date": {"$ne": None, "$regex": r"^\d{4}-\d{2}-\d{2}"}
            }
        },
        {
            "$addFields": {
                "year": {
                    "$year": {
                        "$dateFromString": {
                            "dateString": "$release_date",
                            "format": "%Y-%m-%d"
                        }
                    }
                }
            }
        },
        {
            "$match": {
                "year": {"$ne": None, "$gt": 1800}
            }
        },
        {
            "$group": {
                "_id": "$year",
                "avg_budget": {"$avg": "$budget"},
                "avg_revenue": {"$avg": "$revenue"},
                "avg_rating": {"$avg": "$vote_average"},
                "avg_popularity": {"$avg": "$popularity"},
                "movie_count": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}},
        {"$out": output_collection_name}
    ]

    collection.aggregate(pipeline)
    print(f"-> Re-saved Query 4 safely with clean year IDs to: '{output_collection_name}'")


# -----------------------------
# QUERY 5: Language Diversity & Global Reach
# -----------------------------
def save_language_diversity_global_reach(collection, output_collection_name="query5_language_diversity"):
    pipeline = [
        {
            "$match": {
                "spoken_languages": {"$ne": None, "$not": {"$type": 10}},
                "vote_count": {"$gt": 50}
            }
        },
        {
            "$addFields": {
                "safe_language_string": {
                    "$cond": [
                        {"$eq": ["$spoken_languages", ""]},
                        "Unknown",
                        {"$toString": "$spoken_languages"}
                    ]
                }
            }
        },
        {
            "$addFields": {
                "language_array": {
                    "$split": ["$safe_language_string", ", "]
                }
            }
        },
        {
            "$addFields": {
                "language_count": {
                    "$cond": {
                        "if": {"$isArray": "$language_array"},
                        "then": {"$size": "$language_array"},
                        "else": 1
                    }
                }
            }
        },
        {
            "$match": {
                "language_count": {"$gt": 0}
            }
        },
        {
            "$group": {
                "_id": "$language_count",
                "avg_popularity": {"$avg": "$popularity"},
                "avg_vote_count": {"$avg": "$vote_count"},
                "avg_revenue": {"$avg": "$revenue"},
                "movie_count": {"$sum": 1}
            }
        },
        {
            "$sort": {
                "_id": 1
            }
        },
        {
            "$out": output_collection_name
        }
    ]

    collection.aggregate(pipeline)
    print(f"-> Saved Query 5 safely with clean language count IDs to: '{output_collection_name}'")


# =========================================================
# EXPLAIN OUTPUT
# MongoDB .explain() for Budget vs Success query
# =========================================================

def explain_budget_vs_success(collection):

    command = {
        "aggregate": collection.name,
        "pipeline": [
            {"$match": {"budget": {"$gt": 0}, "revenue": {"$gt": 0}}},
            {
                "$bucket": {
                    "groupBy": "$budget",
                    "boundaries": [0, 1000000, 10000000, 50000000, 100000000, 500000000],
                    "default": "500M+",
                    "output": {
                        "avg_revenue": {"$avg": "$revenue"},
                        "avg_rating": {"$avg": "$vote_average"},
                        "avg_votes": {"$avg": "$vote_count"},
                        "movie_count": {"$sum": 1},
                    },
                }
            },
            {"$sort": {"_id": 1}},
        ],
        "explain": True,
        "cursor": {}
    }

    explanation = collection.database.command(command)

    print("\n--- EXPLAIN: Budget vs Success ---")
    print(explanation)
    return explanation


# =========================================================
# BEFORE & AFTER INDEX COMPARISON
# =========================================================

def runtime_before_after_index(collection):

    pipeline = [
        {"$match": {"budget": {"$gt": 0}, "revenue": {"$gt": 0}}},
        {
            "$bucket": {
                "groupBy": "$budget",
                "boundaries": [0, 1000000, 10000000, 50000000, 100000000, 500000000],
                "default": "500M+",
                "output": {
                    "avg_revenue": {"$avg": "$revenue"},
                    "avg_rating": {"$avg": "$vote_average"},
                    "movie_count": {"$sum": 1},
                },
            }
        },
        {"$sort": {"_id": 1}},
    ]

    # BEFORE index
    start = time.time()
    list(collection.aggregate(pipeline))
    before_time = time.time() - start
    print(f"\n--- Before & After Index Comparison ---")
    print(f"Before index: {before_time:.4f} seconds")

    # Create index on budget
    collection.create_index("budget")
    print("Index created on 'budget'")

    # AFTER index
    start = time.time()
    list(collection.aggregate(pipeline))
    after_time = time.time() - start
    print(f"After index:  {after_time:.4f} seconds")
    print(f"Improvement:  {before_time - after_time:.4f} seconds faster")

    return {
        "before": before_time,
        "after": after_time,
        "improvement": before_time - after_time
    }


# =========================================================
# RUNTIME COMPARISON - 3 Comparable Queries
# =========================================================

def runtime_comparison(collection):

    pipelines = {

        "Budget vs Success": [
            {"$match": {"budget": {"$gt": 0}, "revenue": {"$gt": 0}}},
            {
                "$bucket": {
                    "groupBy": "$budget",
                    "boundaries": [0, 1000000, 10000000, 50000000, 100000000, 500000000],
                    "default": "500M+",
                    "output": {
                        "avg_revenue": {"$avg": "$revenue"},
                        "movie_count": {"$sum": 1},
                    },
                }
            },
            {"$sort": {"_id": 1}},
        ],

        "Engagement vs Revenue by Genre": [
            {
                "$match": {
                    "vote_count": {"$gt": 100},
                    "revenue": {"$gt": 0},
                    "genres": {"$exists": True, "$not": {"$size": 0}},
                }
            },
            {"$unwind": "$genres"},
            {
                "$group": {
                    "_id": "$genres",
                    "avg_vote_count": {"$avg": "$vote_count"},
                    "avg_revenue": {"$avg": "$revenue"},
                    "movie_count": {"$sum": 1},
                }
            },
            {"$sort": {"avg_revenue": -1}},
        ],

        "Film Industry Trends": [
            {
                "$match": {
                    "release_date": {"$ne": None, "$regex": r"^\d{4}-\d{2}-\d{2}"}
                }
            },
            {
                "$addFields": {
                    "year": {
                        "$year": {
                            "$dateFromString": {
                                "dateString": "$release_date",
                                "format": "%Y-%m-%d"
                            }
                        }
                    }
                }
            },
            {"$match": {"year": {"$ne": None, "$gt": 1800}}},
            {
                "$group": {
                    "_id": "$year",
                    "avg_budget": {"$avg": "$budget"},
                    "avg_revenue": {"$avg": "$revenue"},
                    "movie_count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ],
    }

    print("\n--- Runtime Comparison: 3 Queries ---")
    results = {}

    for name, pipeline in pipelines.items():
        start = time.time()
        list(collection.aggregate(pipeline))
        elapsed = time.time() - start
        results[name] = elapsed
        print(f"{name}: {elapsed:.4f} seconds")

    return results


# -----------------------------
# MAIN RUNNER
# -----------------------------
if __name__ == "__main__":

    # 1. Establish connection
    client, db = connect_to_mongodb()

    # 2. Upload source clean dataset
    movies_collection = load_csv_to_mongodb(db, INPUT_FILE)

    print("\nExecuting pipelines and writing queries directly into MongoDB collections...")

    # 3. Execute pipelines which generate new collections automatically via {"$out": ...}
    save_budget_vs_success(movies_collection)
    save_engagement_vs_revenue_by_genre(movies_collection)
    save_popular_genres_by_country(movies_collection)
    save_film_industry_trends(movies_collection)
    save_language_diversity_global_reach(movies_collection)

    print("\nAll queries saved successfully. You can now view them inside your MongoDB viewer (Compass/Shell)!")

    # -----------------------------
    # Performance Analysis
    # -----------------------------

    explain_budget_vs_success(movies_collection)
    runtime_before_after_index(movies_collection)
    runtime_comparison(movies_collection)

    client.close()
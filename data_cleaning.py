import pandas as pd
import ast

# -----------------------------
# CONFIG
# -----------------------------
INPUT_FILE = "TMDB_cleaned_revenue.csv"
OUTPUT_FILE = "TMDB_CLEAN_FINAL.csv"


# -----------------------------
# CLEAN STRING LISTS
# -----------------------------
def split_list(value):
    if not isinstance(value, str):
        return []
    try:
        result = ast.literal_eval(value)
        if isinstance(result, list):
            return [str(x).strip() for x in result]
    except (ValueError, SyntaxError):
        pass
    # fallback for plain comma-separated strings
    return [x.strip() for x in value.split(",") if x.strip()]


# -----------------------------
# CLEAN DATASET
# -----------------------------
def clean_dataset(df):

    print("Initial rows:", len(df))

    # -------------------------
    # DROP COMPLETELY EMPTY ROWS
    # -------------------------
    df = df.dropna(subset=["release_date", "genres", "production_countries"])

    # -------------------------
    # CLEAN NUMERIC FIELDS
    # -------------------------
    numeric_cols = ["budget", "revenue", "vote_average", "vote_count", "popularity"]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # -------------------------
    # CLEAN RELEASE DATE
    # -------------------------
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")

    df = df.dropna(subset=["release_date"])

    # Optional: filter unrealistic dates
    df = df[df["release_date"].dt.year.between(1900, 2025)]

    # -------------------------
    # REMOVE EMPTY LISTS AFTER CLEANING
    # -------------------------
    df = df[
        df["genres"].map(len) > 0
    ]
    df = df[
        df["production_countries"].map(len) > 0
    ]

    # -------------------------
    # RESET INDEX
    # -------------------------
    df = df.reset_index(drop=True)

    print("Final rows:", len(df))

    return df


# -----------------------------
# MAIN
# -----------------------------
def main():

    print("Loading dataset...")
    df = pd.read_csv(INPUT_FILE)

    df = clean_dataset(df)

    print("Saving cleaned dataset...")

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
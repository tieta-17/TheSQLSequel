import pandas as pd

# dataset contains 1 million + movies
# randomly sample 25k movies so that we can operate on the dataset

movies_df = pd.read_csv("TMDB_movie_dataset_v11.csv")

# random_state = 42 for reproducibility
sampled_df = movies_df.sample(n = 25000, random_state = 42)

sampled_df.to_csv('TMDB_movie_dataset_25k_samples.csv')


# Project 2: Databases and Dashboards
##  TheSQLSequel - Basic Introduction
We utilized the kaggle TMDB - "The Movie Database" to construct our dataset and create our queries. This dataset is usable for this project as it has over the required 5,000 entries, 4+ tables or logical entities, numerical/categorical/time entries/fields, as well as relationships between entries. 

After preliminary cleaning, we identified that the 'revenue' column of the dataset contained 98% null values. We opted to filter only entries that have a valid revenue value, cutting our dataset size down to approximately 24 thousand entries. The scripts for data preprocessing and cleaning can be found under /data_cleaning

Logical Entities: Exists independently of a single movie
- Movie (the main entity)
- Genre (categorical classification )
- Production Company
- Production Country 
- Language

## Necessary Packages:

Ensure you have python installed

Necessary packages to install:
`pip install pandas plotly pymongo streamlit pymysql sqlalchemy`

## Analytical Questions:
1. Does a higher production budget actually lead to better outcomes? (either revenue or popularity)
2. Do movies with higher audience engagement (vote_count) tend to have higher financial performance (revenue), and does this relationship vary by genre?
3. What are the most popular genres in each country or region?
4. How has the film industry changed over time? (more expensive, more profitable, lower/higher ratings)

## Additional Information
Primary Keys: ids (movie_id, genre_id, company_id, country_code, language_code)

To run streamlit app, after installing streamlit via
`pip install streamlit`
call 
`streamlit run streamlit_app.py`
in the terminal.

## Sources and Links:

Source: https://www.kaggle.com/datasets/asaniczka/tmdb-movies-dataset-2023-930k-movies/data?select=TMDB_movie_dataset_v11.csv 

Medium Article: https://medium.com/@awesterlund/building-two-databases-on-the-same-dataset-mysql-vs-mongodb-on-24-000-movies-649fc0d0920e

Presentation: https://canva.link/vat1hih9owpme0p 

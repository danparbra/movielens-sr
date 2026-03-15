import sqlite3
from pathlib import Path
from typing import List, Optional

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.backend.user import init_db, load_users_from_dat, login, register

MODEL_PATH = Path(__file__).parent.parent.parent / 'artifacts/models/cf_model_uu_pearson.joblib'
MOVIES_PATH = Path(__file__).parent.parent.parent / 'artifacts/data/movies.dat'
DB_PATH = Path(__file__).parent.parent.parent / 'users.db'

# Load collaborative filtering model
model = joblib.load(MODEL_PATH)

# Load movies
MOVIES = {}
with open(MOVIES_PATH, 'r', encoding='latin-1') as f:
    for line in f:
        parts = line.strip().split('::')
        if len(parts) >= 3:
            MOVIES[int(parts[0])] = {'title': parts[1], 'genres': parts[2]}

app = FastAPI()

class UserLogin(BaseModel):
    user_id: int
    password: str

class UserRegister(BaseModel):
    user_id: int
    password: str
    gender: str
    age: int
    occupation: int
    zipcode: str

class RatingInput(BaseModel):
    user_id: int
    movie_id: int
    rating: float

@app.on_event('startup')
def startup_event():
    init_db()
    load_users_from_dat(20)

@app.post('/login')
def api_login(user: UserLogin):
    if login(str(user.user_id), user.password):
        return {"success": True}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post('/register')
def api_register(user: UserRegister):
    if register(str(user.user_id), user.password, user.gender, user.age, user.occupation, user.zipcode):
        return {"success": True}
    raise HTTPException(status_code=400, detail="User already exists")

@app.get('/recommend/{user_id}')
def recommend(user_id: int, top_n: int = 5):
    # Recommend top N unrated movies for the user
    # For demo, use model.predict(user_id, movie_id) for all movies
    # In practice, use model's API for batch prediction
    rated_movies = get_user_rated_movies(user_id)
    unrated_movies = [mid for mid in MOVIES if mid not in rated_movies]
    preds = []
    for mid in unrated_movies:
        try:
            pred = model.predict(user_id, mid)
            preds.append((mid, pred.est))
        except Exception:
            continue
    preds.sort(key=lambda x: x[1], reverse=True)
    top = preds[:top_n]
    return [{"movie_id": mid, "title": MOVIES[mid]['title'], "predicted_rating": float(r)} for mid, r in top]

def get_user_rated_movies(user_id: int):
    # For demo, read ratings from ratings.dat
    RATINGS_PATH = Path(__file__).parent.parent.parent / 'artifacts/data/ratings.dat'
    rated = set()
    with open(RATINGS_PATH, 'r') as f:
        for line in f:
            parts = line.strip().split('::')
            if len(parts) >= 3 and int(parts[0]) == user_id:
                rated.add(int(parts[1]))
    return rated

@app.post('/rate')
def rate_movie(rating: RatingInput):
    # For demo, just print/store in a local SQLite table
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ratings (user_id INTEGER, movie_id INTEGER, rating REAL)''')
    c.execute('INSERT INTO ratings (user_id, movie_id, rating) VALUES (?, ?, ?)',
              (rating.user_id, rating.movie_id, rating.rating))
    conn.commit()
    conn.close()
    return {"success": True}

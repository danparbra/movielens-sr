import pandas as pd
from pathlib import Path
import gc

# -----------------------------
# Parámetros
# -----------------------------
MIN_USER_RATINGS = 50
MIN_MOVIE_RATINGS = 50
SAMPLE_SIZE = 20000000
TEST_SIZE = 0.3
RANDOM_STATE = 42

OUTPUT_DIR = Path("preprocessing/splits")
OUTPUT_DIR.mkdir(exist_ok=True)

# -----------------------------
# 1. Cargar ratings
# -----------------------------
ratings = pd.read_csv("preprocessing/data/rating.csv")

# Nos quedamos solo con las columnas necesarias
ratings = ratings[["userId", "movieId", "rating"]].copy()

print("Shape original:", ratings.shape)
print(ratings.head())

# -----------------------------
# 2. Sample de 10 millones
# -----------------------------
ratings = ratings.sample(
    n=SAMPLE_SIZE,
    random_state=RANDOM_STATE
).reset_index(drop=True)

print("Shape después del sample:", ratings.shape)

# -----------------------------
# 2. Filtrado iterativo
#    usuarios > 50 ratings
#    películas > 50 ratings
# -----------------------------
def filter_users_movies(df, min_user_ratings=50, min_movie_ratings=50):
    prev_shape = None
    current_df = df.copy()

    while prev_shape != current_df.shape:
        prev_shape = current_df.shape

        # Filtrar usuarios
        user_counts = current_df["userId"].value_counts()
        valid_users = user_counts[user_counts > min_user_ratings].index
        current_df = current_df[current_df["userId"].isin(valid_users)]

        # Filtrar películas
        movie_counts = current_df["movieId"].value_counts()
        valid_movies = movie_counts[movie_counts > min_movie_ratings].index
        current_df = current_df[current_df["movieId"].isin(valid_movies)]

    return current_df.reset_index(drop=True)


filtered_ratings = filter_users_movies(
    ratings,
    min_user_ratings=MIN_USER_RATINGS,
    min_movie_ratings=MIN_MOVIE_RATINGS
)

print("\nShape después del filtrado:", filtered_ratings.shape)
print("Usuarios:", filtered_ratings["userId"].nunique())
print("Películas:", filtered_ratings["movieId"].nunique())


# -----------------------------
# 3. Split por usuario
# -----------------------------
def train_test_split_by_user(df, test_size=0.2, random_state=42):
    train_parts = []
    test_parts = []

    for user_id, user_df in df.groupby("userId"):
        user_df = user_df.sample(frac=1, random_state=random_state)  # shuffle

        n_ratings = len(user_df)
        n_test = max(1, int(round(n_ratings * test_size)))

        # Para asegurar que quede al menos 1 rating en train
        if n_test >= n_ratings:
            n_test = n_ratings - 1

        test_user = user_df.iloc[:n_test]
        train_user = user_df.iloc[n_test:]

        train_parts.append(train_user)
        test_parts.append(test_user)

    train_df = pd.concat(train_parts).reset_index(drop=True)
    test_df = pd.concat(test_parts).reset_index(drop=True)

    return train_df, test_df


train_df, test_df = train_test_split_by_user(
    filtered_ratings,
    test_size=TEST_SIZE,
    random_state=RANDOM_STATE
)

# Orden
train_df = train_df.sort_values(["userId", "movieId"]).reset_index(drop=True)
test_df = test_df.sort_values(["userId", "movieId"]).reset_index(drop=True)

print("\nTrain shape:", train_df.shape)
print("Test shape:", test_df.shape)

print("\nColumnas train:", train_df.columns.tolist())
print("Columnas test:", test_df.columns.tolist())


# -----------------------------
# 4. Verificaciones
# -----------------------------
assert list(train_df.columns) == ["userId", "movieId", "rating"]
assert list(test_df.columns) == ["userId", "movieId", "rating"]

# Usuarios en test deben existir en train
users_in_test_not_in_train = set(test_df["userId"].unique()) - set(train_df["userId"].unique())
print("\nUsuarios en test que no están en train:", len(users_in_test_not_in_train))

# Películas en test que no están en train (puede pasar raro, pero aquí no debería ser común)
movies_in_test_not_in_train = set(test_df["movieId"].unique()) - set(train_df["movieId"].unique())
print("Películas en test que no están en train:", len(movies_in_test_not_in_train))


# -----------------------------
# 5. Guardar archivos
# -----------------------------
train_path = OUTPUT_DIR / "train_ratings.csv"
test_path = OUTPUT_DIR / "test_ratings.csv"

train_df.to_csv(train_path, index=False)
test_df.to_csv(test_path, index=False)

print(f"\nArchivo train guardado en: {train_path}")
print(f"Archivo test guardado en: {test_path}")

# -----------------------------
# 6. Liberar memoria
# -----------------------------
del ratings
del filtered_ratings
del train_df
del test_df

print("Memoria liberada.")
# movielens-sr
Uniandes – Sistemas de Recomendación MINE4201

## Correr aplicación
1. Descargar código
```bash
git clone git@github.com:danparbra/movielens-sr.git
```

```bash
cd movielens-sr/
```

2. Construir container
```bash
docker build -t movielens-app .
```

3. Correr
```bash
docker run -p 8000:8000 -p 8501:8501 movielens-app
```
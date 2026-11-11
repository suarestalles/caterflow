from fastapi import FastAPI

# 1. Cria a instância principal do FastAPI
app = FastAPI(
    title="Minha API",
    version="1.0.0",
    description="Exemplo de projeto FastAPI"
)

# 2. Define uma rota (endpoint) básica
@app.get("/")
def read_root():
    return {"message": "Olá, Mundo!"}

# 3. Exemplo de rota com parâmetro
@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
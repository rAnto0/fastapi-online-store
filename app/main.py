from fastapi import FastAPI

app = FastAPI(title="Shop API")


@app.get("/")
async def root():
    return {"message": "Welcome to the Shop API"}

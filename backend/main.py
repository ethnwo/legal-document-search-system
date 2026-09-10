from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Legal Document Retrieval API is running"}
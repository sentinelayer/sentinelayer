from fastapi import FastAPI

app = FastAPI(title="SentinelLayer - Simple Test")

@app.get("/")
def root():
    return {"message": "Hello, SentinelLayer!"}

@app.get("/health")
def health():
    return {"status": "healthy"}

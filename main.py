from app.api.server import app
import uvicorn

def main():
    uvicorn.run(app, host="localhost", port=8000)

if __name__ == "__main__":
    main()

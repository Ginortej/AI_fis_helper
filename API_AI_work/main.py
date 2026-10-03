from fastapi import FastAPI, Depends
from config import settings
import uvicorn



app = FastAPI(title=settings.settings.app_title)




















def main():
    uvicorn.run(app)







if __name__ == "__main__":
    main()

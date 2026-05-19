from fastapi import FastAPI
from app.lifespan import lifespan
from routers import user_router, admin_router, auth_router, grades_router

app = FastAPI(title="School Auth System", lifespan=lifespan)

app.include_router(user_router)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(grades_router)

if __name__ == "__main__":
    import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(app, host="127.0.0.1", port=8000)
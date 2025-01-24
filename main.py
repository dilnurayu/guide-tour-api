from fastapi import FastAPI
from db.base import engine, Base
from router import (
    auth,
    region,
    city,
    address,
    resume,
    review,
    guide,
    tour,
    booking
)

app = FastAPI()

@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        pass

# Include routers
app.include_router(auth.router)
app.include_router(region.router)
app.include_router(city.router)
app.include_router(address.router)
app.include_router(resume.router)
app.include_router(review.router)
app.include_router(guide.router)
app.include_router(tour.router)
app.include_router(booking.router)

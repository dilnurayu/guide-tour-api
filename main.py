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
    booking,
    languages
)
from fastapi.openapi.utils import get_openapi

app = FastAPI()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="UzGuide",
        version="1.0.0",
        description="",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.create_all)
        pass

app.include_router(auth.router)
app.include_router(region.router)
app.include_router(city.router)
app.include_router(address.router)
app.include_router(resume.router)
app.include_router(review.router)
app.include_router(guide.router)
app.include_router(tour.router)
app.include_router(booking.router)
app.include_router(languages.router)




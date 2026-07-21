from fastapi import FastAPI, Request, HTTPException

from .routers.employee import router as employee_router
from .routers.auth import router as auth_router
from .routers.file import router as file_router
from .routers.notification import router as notification_router

from .middleware.logging import log_requests

from .exceptions.handlers import (
    http_exception_handler,
    global_exception_handler,
)

app = FastAPI()


# -------------------
# Routers
# -------------------
# app.include_router(employee_router)
# app.include_router(auth_router)
# app.include_router(file_router)
# app.include_router(notification_router)


@app.get("/")
async def root():
    return {"message": "Azure Working"}


# -------------------
# Middleware
# -------------------
@app.middleware("http")
async def logging_middleware(
    request: Request,
    call_next,
):
    return await log_requests(
        request,
        call_next,
    )


# -------------------
# Exception Handlers
# -------------------
app.add_exception_handler(
    HTTPException,
    http_exception_handler,
)

app.add_exception_handler(
    Exception,
    global_exception_handler,
)

from fastapi import (
    APIRouter,
    BackgroundTasks,
)

from ..services.notification_service import (
    send_welcome_email,
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.post("/welcome-email")
async def welcome_email(
    email: str,
    background_tasks: BackgroundTasks,
):
    background_tasks.add_task(
        send_welcome_email,
        email,
    )

    return {
        "message": "Email scheduled",
    }

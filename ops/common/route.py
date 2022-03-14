# pip install fastapi-mail
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from typing import List
from pydantic import BaseModel, EmailStr
from starlette.requests import Request
from starlette.responses import JSONResponse
from config.config import settings
router = APIRouter()


class EmailSchema(BaseModel):
    email: List[EmailStr]
    body: str
    subject: str


MAIL_CONF = ConnectionConfig(
    MAIL_USERNAME=settings.mail_user,
    MAIL_PASSWORD=settings.mail_pswd,
    MAIL_FROM=settings.mail_user,
    MAIL_PORT='465',
    MAIL_SERVER=settings.mail_server,
    MAIL_TLS=False,
    MAIL_SSL=True,
    # USE_CREDENTIALS=True
)


@router.post("/email")
async def simple_send(email: EmailSchema) -> JSONResponse:
    message = MessageSchema(
        subject=email.dict().get("subject"),
        # List of recipients, as many as you can pass
        recipients=email.dict().get("email"),
        body="<html>{}</html>".format(email.dict().get("body")),
        subtype="html"
    )
    fm = FastMail(MAIL_CONF)
    await fm.send_message(message)
    return JSONResponse(status_code=200, content={"message": "email has been sent"})

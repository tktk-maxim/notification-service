from pydantic import BaseModel, Field, EmailStr


class Employee(BaseModel):
    id: int
    first_name: str
    last_name: str
    middle_name: str | None = Field(default=None, null=True)
    login: str
    password: str
    subdivision_id: int
    email: str | None = "example@gmail.com"
    leader: bool | None = Field(default=False, null=True)
    chat_id: int | None = Field(default=None, null=True)
    telegram_name: str

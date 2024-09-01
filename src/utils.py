
from fastapi import HTTPException
import httpx

from config import settings
from telegram import Bot

from datetime import datetime
from shemas import Employee


async def get_user_by_telegram_name(telegram_name: str) -> Employee:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"http://{settings.user_service_host}:{settings.user_service_port}"
                                    f"/employee/entity_with_params/?telegram_name={telegram_name}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return Employee(**response.json())


async def linking_chat_id_to_user(chat_id: int, user: dict) -> str:
    user["chat_id"] = chat_id
    async with httpx.AsyncClient() as client:
        response = await client.put(f"http://{settings.user_service_host}:{settings.user_service_port}"
                                    f"/employee/{user["id"]}", json=user)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code,
                                detail=f"Your telegram account is not authorized in the employee accounting system")
        return f"Сhat ID:{chat_id} has been successfully assigned to the user with id:{user["id"]}"


async def get_telegram_name(chat_id: int, bot: Bot) -> str:
    chat = await bot.get_chat(chat_id)
    return chat.username


async def send_message(chat_id: int, message: str) -> None:
    bot = Bot(token=settings.telegram_token)
    await bot.send_message(chat_id=chat_id, text=message)


async def checking_tasks_for_time_expiration_and_sending_msg():
    async with httpx.AsyncClient() as client:

        # getting all burning tasks from task-service
        response = await client.get(f"http://{settings.task_service_host}:{settings.task_service_port}"
                                    f"/task/burning_tasks/")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        tasks = response.json()

        for task in tasks:
            current_date = datetime.now().date()

            # getting employee's data
            response = await client.get(f"http://{settings.user_service_host}:{settings.user_service_port}"
                                        f"/employee/card/{task["employee_id"]}")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.text)
            employee = response.json()

            print(employee["employee"]["chat_id"])
            if employee["employee"]["chat_id"] != 0:
                await send_message(employee["employee"]["chat_id"],
                                   f"Please note!\n"
                                   f"{task["name"]}\n"
                                   f"Days left until the task is completed: {
                                   ((datetime.strptime(task["date_of_receiving"], "%Y-%m-%d").date()
                                    - current_date).days + task["estimated_days_to_complete"])}\n"
                                   f"Task: {task["description"]}")

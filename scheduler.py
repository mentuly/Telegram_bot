from apscheduler.schedulers.asyncio import AsyncIOScheduler
from handlers.daily import send_daily_message

def setup_scheduler(bot, user_id: int):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_message, "cron", hour=18, minute=35, args=[bot, user_id])
    scheduler.start()
import os
from datetime import time
import pytz

SEND_TIME_STR = "11:00"

TIMEZONE = pytz.timezone("Europe/Kyiv")

IS_TEST_MODE = SEND_TIME_STR.lower() == "test"

if not IS_TEST_MODE:
    hour, minute = map(int, SEND_TIME_STR.split(":"))
    SEND_TIME = time(hour=hour, minute=minute)
else:
    SEND_TIME = None

BOT_TOKEN = os.getenv("BOT_TOKEN")
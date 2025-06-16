from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class Settings:
    bot_token: str = os.getenv('BOT_TOKEN', '')

settings = Settings()

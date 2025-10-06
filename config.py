import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        # Bot Token
        self.BOT_TOKEN = os.environ.get('BOT_TOKEN')
        if not self.BOT_TOKEN:
            raise ValueError("❌ BOT_TOKEN environment variable is required")
        
        # Owner Configuration
        self.OWNER_ID = int(os.environ.get('OWNER_ID', 0))
        self.OWNER_USERNAME = os.environ.get('OWNER_USERNAME', 'owner_username')
        self.BOT_USERNAME = os.environ.get('BOT_USERNAME', 'your_bot_username')
        
        # MongoDB Configuration
        self.MONGO_URI = os.environ.get('MONGO_URI')
        self.DB_NAME = os.environ.get('DB_NAME', 'course_bot')
        
        # Admin User IDs
        admin_ids = os.environ.get('ADMIN_IDS', '')
        self.ADMINS = [int(id.strip()) for id in admin_ids.split(',') if id.strip()]
        
        # Add owner to admins
        if self.OWNER_ID and self.OWNER_ID not in self.ADMINS:
            self.ADMINS.append(self.OWNER_ID)
        
        # Mega Credentials
        self.MEGA_EMAIL = os.environ.get('MEGA_EMAIL', '')
        self.MEGA_PASSWORD = os.environ.get('MEGA_PASSWORD', '')
        
        # File Size Limits
        self.TELEGRAM_MAX_SIZE = 50 * 1024 * 1024  # 50MB
        self.MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
        
        # Heroku Specific
        self.IS_HEROKU = os.environ.get('IS_HEROKU', False)
        
        if not self.OWNER_ID:
            raise ValueError("❌ OWNER_ID environment variable is required")
            
        print(f"🚀 Heroku Bot Config loaded - Owner: {self.OWNER_ID}")
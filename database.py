import pymongo
import datetime
import random
import string
import json
import os
from config import Config

class MongoDB:
    def __init__(self):
        self.config = Config()
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self):
        """Connect to MongoDB"""
        try:
            if self.config.MONGO_URI:
                self.client = pymongo.MongoClient(self.config.MONGO_URI)
                self.db = self.client[self.config.DB_NAME]
                print("✅ Connected to MongoDB Atlas successfully")
            else:
                raise Exception("No MongoDB URI provided")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            self.setup_local_database()
    
    def setup_local_database(self):
        """Setup local database using JSON files"""
        self.local_db = {
            'users': [],
            'channels': [],
            'premium_users': [],
            'user_files': [],
            'downloads': []
        }
        
        if not os.path.exists('data'):
            os.makedirs('data')
        
        print("⚠️ Using local JSON database")
    
    def save_user(self, user_data):
        """Save or update user information"""
        try:
            if hasattr(self, 'local_db'):
                return self._save_user_local(user_data)
            else:
                self.db.users.update_one(
                    {'user_id': user_data['user_id']},
                    {
                        '$set': {
                            'first_name': user_data['first_name'],
                            'username': user_data.get('username'),
                            'last_activity': datetime.datetime.now()
                        },
                        '$setOnInsert': {
                            'created_at': datetime.datetime.now(),
                            'download_count': 0
                        }
                    },
                    upsert=True
                )
                return True
        except Exception as e:
            print(f"Error saving user: {e}")
            return False
    
    def _save_user_local(self, user_data):
        """Save user to local JSON"""
        try:
            users = self.load_local_data('users')
            existing_user = next((u for u in users if u['user_id'] == user_data['user_id']), None)
            
            if existing_user:
                existing_user.update({
                    'first_name': user_data['first_name'],
                    'username': user_data.get('username'),
                    'last_activity': datetime.datetime.now().isoformat()
                })
            else:
                user_data['created_at'] = datetime.datetime.now().isoformat()
                user_data['download_count'] = 0
                users.append(user_data)
            
            self.save_local_data('users', users)
            return True
        except Exception as e:
            print(f"Error saving user locally: {e}")
            return False
    
    def generate_download_id(self):
        """Generate unique download ID"""
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    def load_local_data(self, collection):
        """Load data from local JSON file"""
        try:
            with open(f'data/{collection}.json', 'r') as f:
                return json.load(f)
        except:
            return self.local_db.get(collection, [])
    
    def save_local_data(self, collection, data):
        """Save data to local JSON file"""
        try:
            with open(f'data/{collection}.json', 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving local data: {e}")
            return False
    
    def get_user(self, user_id):
        """Get user by ID"""
        try:
            if hasattr(self, 'local_db'):
                users = self.load_local_data('users')
                for user in users:
                    if user['user_id'] == user_id:
                        return user
                return None
            else:
                return self.db.users.find_one({'user_id': user_id})
        except:
            return None
    
    def get_total_users(self):
        """Get total user count"""
        try:
            if hasattr(self, 'local_db'):
                users = self.load_local_data('users')
                return len(users)
            else:
                return self.db.users.count_documents({})
        except:
            return 0
    
    def save_premium_user(self, premium_data):
        """Save premium user"""
        try:
            if hasattr(self, 'local_db'):
                premium_users = self.load_local_data('premium_users')
                premium_users = [u for u in premium_users if u['user_id'] != premium_data['user_id']]
                premium_users.append(premium_data)
                self.save_local_data('premium_users', premium_users)
                return True
            else:
                self.db.premium_users.update_one(
                    {'user_id': premium_data['user_id']},
                    {'$set': premium_data},
                    upsert=True
                )
                return True
        except Exception as e:
            print(f"Error saving premium user: {e}")
            return False
    
    def get_premium_user(self, user_id):
        """Get premium user"""
        try:
            if hasattr(self, 'local_db'):
                premium_users = self.load_local_data('premium_users')
                for user in premium_users:
                    if user['user_id'] == user_id and user.get('active', True):
                        return user
                return None
            else:
                return self.db.premium_users.find_one({
                    'user_id': user_id,
                    'active': True
                })
        except:
            return None
    
    def get_all_premium_users(self):
        """Get all premium users"""
        try:
            if hasattr(self, 'local_db'):
                return self.load_local_data('premium_users')
            else:
                return list(self.db.premium_users.find({'active': True}))
        except:
            return []
    
    def deactivate_premium_user(self, user_id):
        """Deactivate premium user"""
        try:
            if hasattr(self, 'local_db'):
                premium_users = self.load_local_data('premium_users')
                for user in premium_users:
                    if user['user_id'] == user_id:
                        user['active'] = False
                self.save_local_data('premium_users', premium_users)
                return True
            else:
                self.db.premium_users.update_one(
                    {'user_id': user_id},
                    {'$set': {'active': False}}
                )
                return True
        except:
            return False
    
    def save_channel(self, channel_data):
        """Save channel"""
        try:
            if hasattr(self, 'local_db'):
                channels = self.load_local_data('channels')
                channels = [c for c in channels if c['channel_id'] != channel_data['channel_id']]
                channels.append(channel_data)
                self.save_local_data('channels', channels)
                return True
            else:
                self.db.channels.update_one(
                    {'channel_id': channel_data['channel_id']},
                    {'$set': channel_data},
                    upsert=True
                )
                return True
        except Exception as e:
            print(f"Error saving channel: {e}")
            return False
    
    def get_channels(self):
        """Get all channels"""
        try:
            if hasattr(self, 'local_db'):
                return self.load_local_data('channels')
            else:
                return list(self.db.channels.find({}))
        except:
            return []
    
    def delete_channel(self, channel_id):
        """Delete channel"""
        try:
            if hasattr(self, 'local_db'):
                channels = self.load_local_data('channels')
                channels = [c for c in channels if c['channel_id'] != channel_id]
                self.save_local_data('channels', channels)
                return True
            else:
                self.db.channels.delete_one({'channel_id': channel_id})
                return True
        except:
            return False
    
    def save_user_file(self, file_data):
        """Save user file"""
        try:
            if hasattr(self, 'local_db'):
                user_files = self.load_local_data('user_files')
                user_files.append(file_data)
                self.save_local_data('user_files', user_files)
                return True
            else:
                self.db.user_files.insert_one(file_data)
                return True
        except Exception as e:
            print(f"Error saving user file: {e}")
            return False
    
    def get_user_files(self, user_id):
        """Get user files"""
        try:
            if hasattr(self, 'local_db'):
                user_files = self.load_local_data('user_files')
                return [f for f in user_files if f['user_id'] == user_id and f.get('active', True)]
            else:
                return list(self.db.user_files.find({
                    'user_id': user_id,
                    'active': True
                }))
        except:
            return []
    
    def log_download(self, download_data):
        """Log download"""
        try:
            if hasattr(self, 'local_db'):
                downloads = self.load_local_data('downloads')
                downloads.append(download_data)
                self.save_local_data('downloads', downloads)
                return True
            else:
                self.db.downloads.insert_one(download_data)
                return True
        except Exception as e:
            print(f"Error logging download: {e}")
            return False
    
    def update_download_status(self, download_id, status, error_message=None):
        """Update download status"""
        try:
            if hasattr(self, 'local_db'):
                downloads = self.load_local_data('downloads')
                for download in downloads:
                    if download.get('download_id') == download_id:
                        download['status'] = status
                        download['completed_at'] = datetime.datetime.now().isoformat()
                        if error_message:
                            download['error_message'] = error_message
                self.save_local_data('downloads', downloads)
                return True
            else:
                update_data = {
                    'status': status,
                    'completed_at': datetime.datetime.now()
                }
                if error_message:
                    update_data['error_message'] = error_message
                
                self.db.downloads.update_one(
                    {'download_id': download_id},
                    {'$set': update_data}
                )
                return True
        except Exception as e:
            print(f"Error updating download status: {e}")
            return False
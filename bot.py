import os
import logging
import asyncio
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from config import Config
from database import MongoDB

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class SimpleCourseBot:
    def __init__(self):
        self.config = Config()
        self.db = MongoDB()
        
        # For testing - simple premium users list
        self.premium_users = [self.config.OWNER_ID] + self.config.ADMINS
        
        print("🤖 Bot initialized successfully!")
    
    async def start(self, update: Update, context: CallbackContext):
        user = update.effective_user
        user_id = user.id
        
        # Save user to database
        self.db.save_user({
            'user_id': user_id,
            'first_name': user.first_name,
            'username': user.username,
            'last_activity': 'now()'
        })
        
        if user_id == self.config.OWNER_ID:
            await update.message.reply_text(
                "👑 **OWNER PANEL**\n\n"
                "Welcome back! Here are your commands:\n\n"
                "💎 /premium - Manage premium users\n"
                "📢 /broadcast - Broadcast message\n"
                "📊 /stats - Bot statistics\n"
                "📁 /myfiles - Your downloaded files\n"
                "🔗 /add_channel - Add upload channel"
            )
        elif user_id in self.config.ADMINS:
            await update.message.reply_text(
                "⚡ **ADMIN PANEL**\n\n"
                "Welcome! Admin commands available.\n\n"
                "💎 /premium - Manage users\n"
                "📊 /stats - Statistics\n"
                "👑 Owner: @" + self.config.OWNER_USERNAME
            )
        elif user_id in self.premium_users:
            await update.message.reply_text(
                "🎉 **PREMIUM USER**\n\n"
                "Welcome back! You have premium access.\n\n"
                "🚀 **You can:**\n"
                "• Download Mega links\n"
                "• Get files in your storage\n"
                "• Auto upload to channels\n\n"
                "💡 **Just send any Mega.nz link to start!**\n\n"
                "📁 /myfiles - Your downloaded files"
            )
        else:
            await update.message.reply_text(
                "🔒 **PREMIUM BOT**\n\n"
                "Hi! This is an exclusive premium bot.\n\n"
                "💎 **Features:**\n"
                "• 5GB File Support\n"
                "• Auto Channel Upload\n"
                "• Personal File Storage\n\n"
                "📧 **Contact Owner:** @" + self.config.OWNER_USERNAME + "\n"
                "🆔 **Your ID:** `" + str(user_id) + "`\n\n"
                "💰 **Message owner with your ID for premium access**"
            )
    
    async def premium_command(self, update: Update, context: CallbackContext):
        """Manage premium users"""
        user_id = update.effective_user.id
        
        # Only owner and admins can manage premium users
        if user_id != self.config.OWNER_ID and user_id not in self.config.ADMINS:
            await update.message.reply_text("❌ Only owner and admins can manage premium users.")
            return
        
        if not context.args:
            # Show premium management panel
            premium_count = len([u for u in self.premium_users if u not in [self.config.OWNER_ID] + self.config.ADMINS])
            
            premium_text = f"""
💎 **PREMIUM USER MANAGEMENT**

👑 **Owner:** @{self.config.OWNER_USERNAME}
📊 **Total Premium Users:** {premium_count}

🛠 **Commands:**
/premium add <user_id> - Add premium user
/premium remove <user_id> - Remove premium user
/premium list - List all premium users
/premium check <user_id> - Check user status
"""
            await update.message.reply_text(premium_text)
            return
        
        action = context.args[0].lower()
        
        if action == 'add' and len(context.args) >= 2:
            try:
                target_user_id = int(context.args[1])
                if target_user_id not in self.premium_users:
                    self.premium_users.append(target_user_id)
                    
                    # Save to database
                    self.db.save_premium_user({
                        'user_id': target_user_id,
                        'added_by': user_id,
                        'added_date': 'now()',
                        'active': True,
                        'downloads_count': 0
                    })
                    
                    # Try to notify the user
                    try:
                        await context.bot.send_message(
                            chat_id=target_user_id,
                            text=f"""
🎉 **CONGRATULATIONS!**

You've been granted **PREMIUM ACCESS** to the course bot!

✅ **Now you can:**
• Download any Mega link
• Get files in your personal storage
• Auto upload to owner's channel

🚀 **Simply send any Mega link to start downloading!**

👑 **Bot Owner:** @{self.config.OWNER_USERNAME}
                            """
                        )
                    except:
                        pass
                    
                    await update.message.reply_text(f"✅ Premium access granted to user {target_user_id}")
                else:
                    await update.message.reply_text("✅ User already has premium access")
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID. Please provide a numeric ID.")
        
        elif action == 'remove' and len(context.args) >= 2:
            try:
                target_user_id = int(context.args[1])
                if target_user_id in self.premium_users and target_user_id not in [self.config.OWNER_ID] + self.config.ADMINS:
                    self.premium_users.remove(target_user_id)
                    self.db.deactivate_premium_user(target_user_id)
                    await update.message.reply_text(f"✅ Premium access removed from user {target_user_id}")
                else:
                    await update.message.reply_text("❌ User not found or cannot remove owner/admin")
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID")
        
        elif action == 'list':
            premium_text = "📋 **Premium Users:**\n\n"
            
            for user_id in self.premium_users:
                user_info = self.db.get_user(user_id) or {}
                username = user_info.get('username', 'N/A')
                
                if user_id == self.config.OWNER_ID:
                    premium_text += f"👑 Owner: @{username} (ID: {user_id})\n"
                elif user_id in self.config.ADMINS:
                    premium_text += f"⚡ Admin: @{username} (ID: {user_id})\n"
                else:
                    premium_text += f"💎 User: @{username} (ID: {user_id})\n"
            
            await update.message.reply_text(premium_text)
        
        elif action == 'check' and len(context.args) >= 2:
            try:
                target_user_id = int(context.args[1])
                is_premium = target_user_id in self.premium_users
                user_info = self.db.get_user(target_user_id) or {}
                
                check_text = f"""
📋 **User Check**

🆔 **User ID:** {target_user_id}
👤 **Username:** @{user_info.get('username', 'N/A')}
💎 **Premium Status:** {'✅ ACTIVE' if is_premium else '❌ INACTIVE'}
"""
                await update.message.reply_text(check_text)
            except ValueError:
                await update.message.reply_text("❌ Invalid user ID")
    
    async def stats_command(self, update: Update, context: CallbackContext):
        """Show bot statistics"""
        user_id = update.effective_user.id
        
        if user_id != self.config.OWNER_ID and user_id not in self.config.ADMINS:
            await update.message.reply_text("❌ Admin access required.")
            return
        
        total_users = self.db.get_total_users()
        premium_count = len([u for u in self.premium_users if u not in [self.config.OWNER_ID] + self.config.ADMINS])
        
        stats_text = f"""
📊 **BOT STATISTICS**

👥 **Total Users:** {total_users}
💎 **Premium Users:** {premium_count}
⚡ **Admins:** {len(self.config.ADMINS)}
👑 **Owner:** @{self.config.OWNER_USERNAME}

🤖 **Bot:** @{self.config.BOT_USERNAME}
"""
        await update.message.reply_text(stats_text)
    
    async def myfiles_command(self, update: Update, context: CallbackContext):
        """Show user's downloaded files"""
        user_id = update.effective_user.id
        
        if user_id not in self.premium_users:
            await update.message.reply_text(f"❌ Premium feature. Contact @{self.config.OWNER_USERNAME} for access.")
            return
        
        user_files = self.db.get_user_files(user_id)
        
        if not user_files:
            await update.message.reply_text("""
📭 **Your File Storage**

You haven't downloaded any files yet.

🚀 **To get started:**
1. Send any Mega.nz link
2. File will be saved here automatically
3. Access your files anytime

💡 **Try sending a Mega link now!**
            """)
            return
        
        files_text = f"📚 **Your Downloaded Files**\n\n"
        files_text += f"📊 **Total Files:** {len(user_files)}\n\n"
        
        for i, file_info in enumerate(user_files[:5], 1):
            files_text += f"{i}. 📁 {file_info.get('file_name', 'Unknown')}\n"
            files_text += f"   📅 {file_info.get('downloaded_at', 'Unknown')}\n\n"
        
        if len(user_files) > 5:
            files_text += f"... and {len(user_files) - 5} more files\n"
        
        files_text += "\n💡 **Send any Mega link to add more files!**"
        
        await update.message.reply_text(files_text)
    
    async def add_channel_command(self, update: Update, context: CallbackContext):
        """Add channel for auto-upload"""
        user_id = update.effective_user.id
        
        if user_id != self.config.OWNER_ID:
            await update.message.reply_text("❌ Only owner can add channels.")
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /add_channel <channel_id> <channel_name>\n\n"
                "Example: /add_channel -1001234567890 \"My Course Channel\""
            )
            return
        
        channel_id = context.args[0]
        channel_name = context.args[1]
        
        success = self.db.save_channel({
            'channel_id': channel_id,
            'name': channel_name,
            'added_by': user_id,
            'added_date': 'now()'
        })
        
        if success:
            await update.message.reply_text(f"✅ Channel '{channel_name}' added successfully!")
        else:
            await update.message.reply_text("❌ Failed to add channel")
    
    async def broadcast_command(self, update: Update, context: CallbackContext):
        """Broadcast message to all users"""
        user_id = update.effective_user.id
        
        if user_id != self.config.OWNER_ID:
            await update.message.reply_text("❌ Only owner can broadcast messages.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /broadcast <message>")
            return
        
        message = ' '.join(context.args)
        users_data = self.db.load_local_data('users') if hasattr(self.db, 'local_db') else []
        
        broadcast_msg = await update.message.reply_text(f"📢 Broadcasting to {len(users_data)} users...")
        
        success_count = 0
        for user in users_data:
            try:
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=f"📢 **Announcement from Owner:**\n\n{message}\n\n👑 @{self.config.OWNER_USERNAME}",
                    parse_mode='HTML'
                )
                success_count += 1
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                print(f"Failed to send to {user['user_id']}: {e}")
        
        await broadcast_msg.edit_text(f"✅ Broadcast completed: {success_count}/{len(users_data)} users received")
    
    async def handle_message(self, update: Update, context: CallbackContext):
        """Handle all text messages including Mega links"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        # Check if user has premium access
        if user_id not in self.premium_users:
            await update.message.reply_text(
                "❌ Premium access required.\n\n"
                f"Contact @{self.config.OWNER_USERNAME} for premium access.\n"
                f"Your ID: `{user_id}`"
            )
            return
        
        # Check if it's a Mega link
        if 'mega.nz' in message_text:
            await self.process_mega_link(update, context, message_text)
        else:
            await update.message.reply_text("Please send a valid Mega.nz link to download files.")
    
    async def process_mega_link(self, update: Update, context: CallbackContext, mega_link: str):
        """Process Mega download request"""
        user_id = update.effective_user.id
        user_info = self.db.get_user(user_id) or {}
        username = user_info.get('username', 'User')
        
        try:
            status_msg = await update.message.reply_text("🔍 Processing your Mega link...")
            
            # Simulate download process
            await asyncio.sleep(2)
            await status_msg.edit_text("⬇️ Downloading from Mega... (This is simulation)")
            
            await asyncio.sleep(3)
            await status_msg.edit_text("📤 Uploading to channels...")
            
            # Simulate file info
            file_name = "course-file.pdf"
            file_size = "150MB"
            download_id = self.db.generate_download_id()
            
            # Log the download
            self.db.log_download({
                'download_id': download_id,
                'user_id': user_id,
                'mega_link': mega_link,
                'status': 'started',
                'started_at': 'now()',
                'file_name': file_name,
                'file_size': file_size
            })
            
            # Save to user's storage
            self.db.save_user_file({
                'user_id': user_id,
                'file_name': file_name,
                'file_size': file_size,
                'download_id': download_id,
                'downloaded_at': 'now()',
                'active': True
            })
            
            # Update download status
            self.db.update_download_status(download_id, 'completed')
            
            # Success message
            success_text = f"""
✅ **DOWNLOAD COMPLETE!**

📁 **File:** {file_name}
💾 **Size:** {file_size}
👤 **Downloaded by:** @{username}

✅ **File saved to your personal storage**
✅ **Uploaded to owner's channels**

📁 Use /myfiles to see all your files

🎉 **Happy Learning!**
            """
            
            await status_msg.edit_text(success_text)
            
        except Exception as e:
            error_msg = f"❌ Error processing your request: {str(e)}"
            await update.message.reply_text(error_msg)
    
    def setup_handlers(self, application):
        """Setup all message handlers"""
        # Command handlers
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.start))
        application.add_handler(CommandHandler("premium", self.premium_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(CommandHandler("myfiles", self.myfiles_command))
        application.add_handler(CommandHandler("add_channel", self.add_channel_command))
        application.add_handler(CommandHandler("broadcast", self.broadcast_command))
        
        # Message handler for Mega links
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.handle_message
        ))

def main():
    try:
        print("🚀 Starting Ultimate Course Bot...")
        
        # Initialize bot
        bot = SimpleCourseBot()
        
        # Create application
        application = Application.builder().token(bot.config.BOT_TOKEN).build()
        
        # Setup handlers
        bot.setup_handlers(application)
        
        # Start bot
        print("✅ Bot is starting...")
        print(f"👑 Owner ID: {bot.config.OWNER_ID}")
        print(f"🤖 Bot Username: {bot.config.BOT_USERNAME}")
        
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Bot failed to start: {e}")
        print("Please check your BOT_TOKEN and OWNER_ID in .env file")

if __name__ == "__main__":
    main()
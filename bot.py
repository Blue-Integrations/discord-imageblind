import discord
from discord.ext import commands
import openai
import os
import io
import aiohttp
from PIL import Image
import logging
import signal
import sys
import asyncio
import time
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)

# OpenAI configuration
openai.api_key = os.getenv('OPENAI_API_KEY')

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    # Exit gracefully
    sys.exit(0)

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

class ImageContextBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.openai_client = openai.AsyncOpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Track user image history
        self.user_image_history = {}  # user_id -> list of image data
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Check if the message contains the trigger phrase
        if "tell me context of image" in message.content.lower():
            await self.handle_image_context_request(message)
        
        # Check for user-specific image context requests
        elif "image context of" in message.content.lower() and "@" in message.content:
            await self.handle_user_image_context_request(message)
    
    async def handle_image_context_request(self, message):
        """Handle requests for image context analysis"""
        try:
            # Check if there are any images in the message
            if not message.attachments:
                # Check if there are any images in the message content (URLs)
                image_urls = await self.extract_image_urls(message.content)
                if not image_urls:
                    await message.author.send("I couldn't find any images to analyze. Please attach an image or provide an image URL along with your request.")
                    return
                
                # Process the first image URL found
                image_url = image_urls[0]
                context = await self.analyze_image_from_url(image_url)
            else:
                # Process attached images
                attachment = message.attachments[0]
                if not self.is_image_file(attachment.filename):
                    await message.author.send("Please attach an image file (PNG, JPG, JPEG, GIF, etc.) for me to analyze.")
                    return
                
                context = await self.analyze_image_from_attachment(attachment)
            
            if context:
                # Store the image context in user's history
                if message.author.id not in self.user_image_history:
                    self.user_image_history[message.author.id] = []
                
                # Store image data (limit to last 10 images per user)
                image_data = {
                    'timestamp': message.created_at,
                    'context': context,
                    'channel': message.channel.name,
                    'guild': message.guild.name if message.guild else 'DM'
                }
                
                self.user_image_history[message.author.id].append(image_data)
                
                # Keep only last 10 images per user
                if len(self.user_image_history[message.author.id]) > 10:
                    self.user_image_history[message.author.id] = self.user_image_history[message.author.id][-10:]
                
                # Notify the user in the channel that we'll send them a DM
                await message.channel.send(f"👁️ **{message.author.display_name}**, I'm analyzing the image and will send you the context via direct message!")
                
                # Send the context privately to the user (with character limit)
                context_preview = context[:1500] + "..." if len(context) > 1500 else context
                await message.author.send(f"**Image Context Analysis:**\n\n{context_preview}")
                
                # If context was truncated, send the rest in a follow-up message
                if len(context) > 1500:
                    remaining_context = context[1500:]
                    chunks = [remaining_context[i:i+1500] for i in range(0, len(remaining_context), 1500)]
                    for i, chunk in enumerate(chunks):
                        await message.author.send(f"**Continued... (Part {i+2}):**\n\n{chunk}")
                
                # Add a reaction to acknowledge the request was processed
                await message.add_reaction('✅')
            else:
                # Notify the user in the channel about the error
                await message.channel.send(f"❌ **{message.author.display_name}**, I encountered an error while analyzing the image. Please try again.")
                await message.author.send("I encountered an error while analyzing the image. Please try again.")
                
        except Exception as e:
            logger.error(f"Error processing image context request: {e}")
            await message.author.send("I encountered an error while processing your request. Please try again later.")
    
    async def handle_user_image_context_request(self, message):
        """Handle requests for image context from a specific user's history"""
        try:
            # Extract mentioned user
            mentioned_user = None
            for mention in message.mentions:
                mentioned_user = mention
                break
            
            if not mentioned_user:
                await message.channel.send("❌ Please mention a user to get their image context. Example: 'image context of @username'")
                return
            
            # Always search for the most recent image (assume it's new)
            await message.channel.send(f"🔍 **{message.author.display_name}**, I'm searching for {mentioned_user.display_name}'s most recent image to analyze...")
            
            # Search recent messages for images from this user
            recent_image = await self.find_recent_user_image(message.channel, mentioned_user)
            
            if recent_image:
                # Analyze the found image
                await message.channel.send(f"📸 Found an image! Analyzing {mentioned_user.display_name}'s recent image...")
                context = await self.analyze_image_with_openai(recent_image['image_data'])
                
                if context:
                    # Store in history (replacing old context if it exists)
                    if mentioned_user.id not in self.user_image_history:
                        self.user_image_history[mentioned_user.id] = []
                    
                    # Check if this is the same image (by timestamp proximity - within 1 hour)
                    is_new_image = True
                    if self.user_image_history[mentioned_user.id]:
                        last_image = self.user_image_history[mentioned_user.id][-1]
                        time_diff = abs((recent_image['timestamp'] - last_image['timestamp']).total_seconds())
                        if time_diff < 3600:  # Less than 1 hour difference
                            is_new_image = False
                    
                    if is_new_image:
                        # Add new image to history
                        image_data = {
                            'timestamp': recent_image['timestamp'],
                            'context': context,
                            'channel': message.channel.name,
                            'guild': message.guild.name if message.guild else 'DM'
                        }
                        
                        self.user_image_history[mentioned_user.id].append(image_data)
                        await message.channel.send(f"🆕 **New image detected!** I've analyzed {mentioned_user.display_name}'s latest image and will send you the context via direct message!")
                    else:
                        await message.channel.send(f"📸 **Same image detected.** I've re-analyzed {mentioned_user.display_name}'s image and will send you the context via direct message!")
                    
                    # Send context to requester (with character limit)
                    context_preview = context[:1500] + "..." if len(context) > 1500 else context
                    await message.author.send(f"**Image Context from {mentioned_user.display_name}'s recent image:**\n\n{context_preview}")
                    
                    # If context was truncated, send the rest in a follow-up message
                    if len(context) > 1500:
                        remaining_context = context[1500:]
                        chunks = [remaining_context[i:i+1500] for i in range(0, len(remaining_context), 1500)]
                        for i, chunk in enumerate(chunks):
                            await message.author.send(f"**Continued... (Part {i+2}):**\n\n{chunk}")
                    
                    await message.add_reaction('✅')
                else:
                    await message.channel.send(f"❌ **{message.author.display_name}**, I couldn't analyze {mentioned_user.display_name}'s image. Please try again.")
            else:
                await message.channel.send(f"❌ **{message.author.display_name}**, I couldn't find any recent images from {mentioned_user.display_name} in this channel.\n\n💡 **Tip**: Make sure they've posted an image recently.")
            
        except Exception as e:
            logger.error(f"Error processing user image context request: {e}")
            await message.channel.send(f"❌ **{message.author.display_name}**, I encountered an error while processing your request. Please try again.")
    
    async def extract_image_urls(self, content):
        """Extract image URLs from message content"""
        import re
        # Simple regex to find image URLs
        url_pattern = r'https?://[^\s<>"]+\.(?:png|jpg|jpeg|gif|webp|bmp)'
        urls = re.findall(url_pattern, content, re.IGNORECASE)
        return urls
    
    def is_image_file(self, filename):
        """Check if a filename is an image file"""
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff'}
        return any(filename.lower().endswith(ext) for ext in image_extensions)
    
    async def analyze_image_from_attachment(self, attachment):
        """Analyze an image from a Discord attachment"""
        try:
            # Download the image
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        return await self.analyze_image_with_openai(image_data)
                    else:
                        logger.error(f"Failed to download image: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error downloading attachment: {e}")
            return None
    
    async def analyze_image_from_url(self, image_url):
        """Analyze an image from a URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        return await self.analyze_image_with_openai(image_data)
                    else:
                        logger.error(f"Failed to download image from URL: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error downloading image from URL: {e}")
            return None
    
    @commands.command(name='status')
    async def status_command(self, ctx):
        """Check bot status and usage instructions"""
        embed = discord.Embed(
            title="👁️ BlindBot Status",
            description="I'm here to help blind users understand images!",
            color=0x00ff00
        )
        embed.add_field(
            name="How to use",
            value="Type **'tell me context of image'** with an attached image or image URL\n\nOr request someone else's image: **'image context of @username'**",
            inline=False
        )
        embed.add_field(
            name="Features",
            value="• Analyzes images using AI\n• Sends descriptions privately\n• Works with attachments and URLs\n• Blind-friendly descriptions\n• Tracks user image history",
            inline=False
        )
        embed.add_field(
            name="Status",
            value="✅ Online and ready to help!",
            inline=False
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='history')
    async def history_command(self, ctx, user: discord.Member = None):
        """View image analysis history for a user (or yourself if no user specified)"""
        target_user = user or ctx.author
        
        if target_user.id not in self.user_image_history or not self.user_image_history[target_user.id]:
            await ctx.send(f"❌ No image analysis history found for {target_user.display_name}.")
            return
        
        # Create embed with user's image history
        embed = discord.Embed(
            title=f"📸 Image History for {target_user.display_name}",
            description=f"Total images analyzed: {len(self.user_image_history[target_user.id])}",
            color=0x0099ff
        )
        
        # Show last 5 images
        recent_images = self.user_image_history[target_user.id][-5:]
        for i, img_data in enumerate(reversed(recent_images), 1):
            timestamp = img_data['timestamp'].strftime("%Y-%m-%d %H:%M")
            channel = img_data['channel']
            embed.add_field(
                name=f"Image {i} ({timestamp})",
                value=f"Channel: {channel}\nContext: {img_data['context'][:100]}...",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='refresh')
    async def refresh_command(self, ctx, user: discord.Member = None):
        """Force refresh and search for recent images from a user"""
        target_user = user or ctx.author
        
        await ctx.send(f"🔍 **{ctx.author.display_name}**, I'm doing a fresh search for recent images from {target_user.display_name}...")
        
        # Force a fresh search
        recent_image = await self.find_recent_user_image(ctx.channel, target_user, limit=200)
        
        if recent_image:
            await ctx.send(f"📸 Found a recent image! Analyzing {target_user.display_name}'s image...")
            context = await self.analyze_image_with_openai(recent_image['image_data'])
            
            if context:
                # Store in history
                if target_user.id not in self.user_image_history:
                    self.user_image_history[target_user.id] = []
                
                image_data = {
                    'timestamp': recent_image['timestamp'],
                    'context': context,
                    'channel': ctx.channel.name,
                    'guild': ctx.guild.name if ctx.guild else 'DM'
                }
                
                self.user_image_history[target_user.id].append(image_data)
                
                await ctx.send(f"✅ **{ctx.author.display_name}**, I've analyzed {target_user.display_name}'s image and will send you the context via direct message!")
                await ctx.author.send(f"**Image Context from {target_user.display_name}'s recent image:**\n\n{context}")
            else:
                await ctx.send(f"❌ **{ctx.author.display_name}**, I couldn't analyze {target_user.display_name}'s image.")
        else:
            await ctx.send(f"❌ **{ctx.author.display_name}**, I couldn't find any recent images from {target_user.display_name} in the last 200 messages.")
    
    @commands.command(name='guide')
    async def guide_command(self, ctx):
        """Show detailed help and usage instructions"""
        embed = discord.Embed(
            title="🆘 BlindBot Guide",
            description="Here's how to use the bot for image context analysis:",
            color=0x0099ff
        )
        
        embed.add_field(
            name="📸 Analyze Your Own Images",
            value="**Command**: `tell me context of image`\n**Usage**: Type this with an attached image or image URL\n**Example**: 'tell me context of image' + [attached image]",
            inline=False
        )
        
        embed.add_field(
            name="👥 Get Someone Else's Image Context",
            value="**Command**: `image context of @username`\n**Usage**: Get context of the mentioned user's most recent image\n**Example**: 'image context of @john'\n**Note**: Bot always analyzes the newest image (assumes it's new)",
            inline=False
        )
        
        embed.add_field(
            name="📚 View Image History",
            value="**Command**: `!history [@username]`\n**Usage**: View your own history or someone else's\n**Example**: `!history` or `!history @john`",
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Check Bot Status",
            value="**Command**: `!status`\n**Usage**: Check if bot is working and see basic info",
            inline=False
        )
        
        embed.add_field(
            name="💡 Getting Started",
            value="1. **First time**: Post an image with 'tell me context of image'\n2. **Build history**: The bot will remember your images\n3. **Share context**: Others can request your image context\n4. **View history**: Use `!history` to see your analyzed images",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='shutdown')
    @commands.has_permissions(administrator=True)
    async def shutdown_command(self, ctx):
        """Gracefully shutdown the bot (Admin only)"""
        await ctx.send("🔄 Shutting down bot gracefully...")
        logger.info(f"Shutdown requested by {ctx.author} in {ctx.guild}")
        # Close the bot gracefully
        await bot.close()
    
    async def analyze_image_with_openai(self, image_data):
        """Analyze image using OpenAI's vision API"""
        try:
            # Convert image data to base64
            import base64
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Create the message for OpenAI
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Provide a concise but detailed description of this image for a blind person. Include:\n- Main objects, people, scenes\n- Layout and positioning\n- Key colors and textures\n- Any readable text\n- Overall mood\n- Notable elements\n\nKeep it under 1500 characters while being descriptive and helpful."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            # Call OpenAI API
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return None
    
    async def find_recent_user_image(self, channel, user, limit=100):
        """Find the most recent image posted by a specific user in a channel"""
        try:
            # Search through recent messages in the channel with cache bypass
            async for message in channel.history(limit=limit, before=None):
                # Skip if message is from a different user
                if message.author.id != user.id:
                    continue
                
                # Check for attached images
                if message.attachments:
                    for attachment in message.attachments:
                        if self.is_image_file(attachment.filename):
                            # Download the image with cache-busting headers
                            async with aiohttp.ClientSession() as session:
                                headers = {
                                    'Cache-Control': 'no-cache',
                                    'Pragma': 'no-cache',
                                    'User-Agent': 'BlindBot/1.0'
                                }
                                async with session.get(attachment.url, headers=headers) as response:
                                    if response.status == 200:
                                        image_data = await response.read()
                                        logger.info(f"Found attached image from {user.display_name} in message {message.id}")
                                        return {
                                            'image_data': image_data,
                                            'timestamp': message.created_at,
                                            'message': message
                                        }
                
                # Check for image URLs in message content
                image_urls = await self.extract_image_urls(message.content)
                if image_urls:
                    image_url = image_urls[0]
                    # Add cache-busting parameter to URL
                    cache_bust_url = f"{image_url}?cb={int(time.time())}"
                    async with aiohttp.ClientSession() as session:
                        headers = {
                            'Cache-Control': 'no-cache',
                            'Pragma': 'no-cache',
                            'User-Agent': 'BlindBot/1.0'
                        }
                        async with session.get(cache_bust_url, headers=headers) as response:
                            if response.status == 200:
                                image_data = await response.read()
                                logger.info(f"Found image URL from {user.display_name} in message {message.id}")
                                return {
                                    'image_data': image_data,
                                    'timestamp': message.created_at,
                                    'message': message
                                }
            
            logger.info(f"No images found for {user.display_name} in last {limit} messages")
            return None
            
        except Exception as e:
            logger.error(f"Error searching for recent user image: {e}")
            return None

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    
    # Set bot status
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening,
        name="for image context requests"
    ))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    logger.error(f"Command error: {error}")

@bot.event
async def on_disconnect():
    logger.info("Bot disconnected from Discord")

@bot.event
async def on_connect():
    logger.info("Bot connected to Discord")

# Add the cog to the bot
async def setup():
    await bot.add_cog(ImageContextBot(bot))

# Run the bot
async def main():
    await setup()
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set!")
        return
    
    try:
        # Start the bot
        await bot.start(token)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down gracefully...")
        await bot.close()
        logger.info("Bot closed successfully")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await bot.close()
        raise

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

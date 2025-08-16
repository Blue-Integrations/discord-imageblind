# BlindBot - Discord Bot for Image Context

A Discord bot that uses OpenAI's vision capabilities to provide detailed image descriptions for blind users. The bot listens for the phrase "tell me context of image" and analyzes any attached images or image URLs, sending the detailed context privately to the user.

## Features

- **Privacy-First**: All image context is sent via private message, not shared in public channels
- **Multiple Input Methods**: Works with both attached images and image URLs
- **Comprehensive Analysis**: Uses OpenAI's GPT-4 Vision to provide detailed, blind-friendly descriptions
- **Easy to Use**: Simply type "tell me context of image" with an image or URL
- **Accessibility Focused**: Descriptions are tailored specifically for blind users

## How It Works

1. User types "tell me context of image" in any Discord channel
2. Bot detects the phrase and looks for images (attachments or URLs)
3. If an image is found, it's sent to OpenAI's vision API for analysis
4. The bot generates a comprehensive, blind-friendly description
5. The description is sent privately to the user via DM
6. A ✅ reaction is added to acknowledge the request was processed

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- OpenAI API Key with access to GPT-4o (includes vision capabilities)

### 1. Clone and Install Dependencies

```bash
git clone <your-repo>
cd blindbot
pip install -r requirements.txt
```

### 2. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Create a bot and copy the token
5. Enable the following bot permissions:
   - Send Messages
   - Read Message History
   - Add Reactions
   - Send Messages in Threads
   - Use Slash Commands

### 3. Configure Environment Variables

Copy the example config file and fill in your tokens:

```bash
cp config.env.example .env
```

Edit `.env` with your actual tokens:

```env
DISCORD_TOKEN=your_actual_discord_bot_token
OPENAI_API_KEY=your_actual_openai_api_key
```

### 4. Invite Bot to Server

Use this URL (replace YOUR_BOT_ID with your actual bot ID):

```
https://discord.com/api/oauth2/authorize?client_id=YOUR_BOT_ID&permissions=2048&scope=bot
```

### 5. Run the Bot

```bash
python bot.py
```

## Usage

### Basic Usage

1. **With Attached Image**: 
   - Attach an image to a message
   - Type "tell me context of image"
   - The bot will analyze the image and send you a private description

2. **With Image URL**:
   - Type "tell me context of image" followed by an image URL
   - Example: "tell me context of image https://example.com/image.jpg"
   - The bot will download and analyze the image

3. **Request Someone Else's Image Context**:
   - Type "image context of @username" to get context of their last analyzed image
   - Example: "image context of @john"
   - The bot will send you the context via private message

### Example Commands

```
tell me context of image
Tell me context of image
TELL ME CONTEXT OF IMAGE
```

The bot is case-insensitive and will respond to any message containing the phrase.

### Bot Commands

- **`!guide`** - Get detailed help and usage instructions
- **`!status`** - Check bot status and get usage instructions
- **`!history [@user]** - View image analysis history for yourself or a specific user
- **`!refresh [@user]** - Force refresh and search for recent images from a user
- **`!shutdown`** - Gracefully shutdown the bot (Admin only)

## What the Bot Describes

The bot provides comprehensive descriptions including:

- Objects, people, and scenes visible
- Layout and positioning of elements
- Colors, textures, and visual details
- Any readable text or signs
- Overall mood and atmosphere
- Notable or unusual elements

## Privacy Features

- **Private Responses**: All image context is sent via direct message
- **No Public Sharing**: Context is never posted in public channels
- **User-Only Access**: Only the requesting user receives the description
- **Minimal Logging**: Bot only logs errors, not user content

## Troubleshooting

### Common Issues

1. **Bot not responding**: Check that the bot has proper permissions and is online
2. **No image found**: Ensure you've attached an image or provided a valid image URL
3. **API errors**: Verify your OpenAI API key is valid and has sufficient credits
4. **Permission denied**: Make sure the bot has permission to send DMs and add reactions

### Logs

The bot logs important events to help with debugging. Check the console output for:
- Connection status
- Error messages
- API call results

## Security Considerations

- Never share your bot token or API keys
- The bot only processes images when explicitly requested
- All API calls are logged for monitoring
- No user data is stored permanently

## Graceful Shutdown

The bot supports graceful shutdown in multiple ways:
- **Signal handling**: Responds to SIGINT (Ctrl+C) and SIGTERM
- **Admin command**: Use `!shutdown` for manual shutdown
- **Clean disconnection**: Properly closes Discord connections
- **Logging**: Records all shutdown events for monitoring

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.

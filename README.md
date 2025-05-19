# Affiliate Marketing Telegram Bot

A Telegram bot for managing affiliate marketing campaigns, offers, and analytics. The bot provides functionality for creating and managing offers, generating reports, and analyzing campaign performance.

## Features

- Offer Management
  - Create and manage affiliate offers
  - View offer details and statistics
  - Track offer performance

- Reporting
  - Generate install reports
  - Track in-app events
  - Post-attribution analysis

- Analytics
  - Campaign performance analysis
  - Media source tracking
  - Custom analytics parameters

## Setup

1. Clone the repository:
```bash
git clone https://github.com/IvanYakov200/AffiliateBot.git
cd AffiliateBot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
Create a `.env` file with the following variables:
```
TELEGRAM_TOKEN=your_telegram_bot_token
APPSFLYER_API_KEY=your_appsflyer_api_key
```

4. Run the bot:
```bash
python src/main.py
```

## Usage

Start the bot in Telegram and use the following commands:
- `/start` - Start working with the bot
- `/help` - Show help information
- `/offers` - List available offers
- `/report` - Generate reports
- `/analyze` - Access analytics features
- `/addoffer` - Add new offer (Admin only)

## Requirements

- Python 3.8+
- python-telegram-bot
- pandas
- requests
- python-dotenv

## License

MIT License 
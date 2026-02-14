# 📡 TeleRadar - Telegram Bulk Phone Number Checker

A powerful tool to check if phone numbers from Excel files are registered on Telegram.

## ✨ Features

- 🚀 **Multi-account support** - Use up to 10 Telegram accounts simultaneously
- 💾 **Checkpoint resume** - Automatically resumes from where it stopped
- 📊 **Excel output** - Color-coded results (YES/NO) with user details
- 🔄 **Flood wait handling** - Smart handling of Telegram rate limits
- 📝 **Detailed logging** - Separate logs for each account
- 🔒 **Secure** - API credentials stored in .env file (not in code)

## 📋 Requirements

- Python 3.8 or higher
- Telegram API credentials (api_id & api_hash)
- Multiple Telegram accounts (optional, for faster checking)

## 🛠️ Installation

```bash
# 1. Clone the repository
git clone https://github.com/ArmanHFahim/TeleRadar.git
cd TeleRadar

# 2. Install required packages
pip install -r requirements.txt

# 3. Create .env file with your API credentials
cp .env.example .env
# Then edit .env with your actual API credentials

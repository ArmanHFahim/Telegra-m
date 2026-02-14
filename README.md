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

\`\`\`bash
# 1. Clone the repository
git clone https://github.com/ArmanHFahim/TeleRadar.git
cd TeleRadar

# 2. Install required packages
pip install -r requirements.txt

# 3. Create .env file with your API credentials
cp .env.example .env
# Then edit .env with your actual API credentials
\`\`\`

## 🔧 Configuration

### Get Telegram API Credentials
1. Go to https://my.telegram.org/apps
2. Login with your phone number
3. Copy **api_id** and **api_hash**
4. Update the \`.env\` file:
\`\`\`
API_ID=your_api_id_here
API_HASH=your_api_hash_here
\`\`\`

## 🚀 Usage Guide

### Step 1: Create Session (First Time Only)
\`\`\`bash
python start.py
\`\`\`

### Step 2: Prepare Excel File
Create \`bd_numbers_state.xlsx\` with a column named **phone**:
| phone |
|-------|
| 8801815797688 |
| 8801815894778 |

### Step 3: Run the Checker

#### Option A: Multiple Accounts (Fastest - Recommended)
\`\`\`bash
python multiple_acc.py
\`\`\`

#### Option B: Single Account
\`\`\`bash
python check_excel_numbers.py
\`\`\`

#### Option C: Detailed UI Version
\`\`\`bash
python tgphonedetail.py
\`\`\`

## 📂 Output Files

| File | Description |
|------|-------------|
| \`checked_results/yes_acc*.xlsx\` | Found Telegram accounts |
| \`checkpoint_acc*.csv\` | Checkpoint files for resuming |
| \`telegram_checker_acc*.log\` | Detailed logs per account |
| \`telegram_checker.log\` | Main log file |

## 📊 Output Format

The Excel output includes:
- ✅ **YES** - Telegram account exists (green highlight)
- ❌ **NO** - No Telegram account (red highlight)
- User details: username, first name, last name, telegram_id
- Premium status, verification status, last seen info

## ⚠️ Important Notes

1. **Rate Limits**: Telegram restricts rapid requests. The tool handles flood waits automatically.
2. **Batch Size**: Default is 20 numbers per batch. Don't increase too much.
3. **Session Files**: Never upload \`.session\` files to GitHub (they're in .gitignore).
4. **API Credentials**: Never share your \`.env\` file or API credentials.

## 🔧 Troubleshooting

### "Session not authorized"
Run \`python start.py\` first to authorize.

### "Flood wait error"
Normal behavior. The tool will wait automatically.

### Module not found
\`\`\`bash
pip install -r requirements.txt --upgrade
\`\`\`

## 🤝 Contributing
Feel free to fork this repository and submit pull requests.

## 📞 Contact
- **Creator**: ArmanHFahim
- **Repository**: [github.com/ArmanHFahim/TeleRadar](https://github.com/ArmanHFahim/TeleRadar)

## 📜 License
This project is open source and available under the MIT License.

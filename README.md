# Ghost-Sol-Monitor v1.0

A lightweight, resilient Solana token monitor using DexScreener API and Telegram Alerts. Designed for traders and developers who need reliable, real-time market movement detection without complex infrastructure.

## 🚀 Features
- **Real-time Price Tracking**: Monitors price fluctuations via the DexScreener API.
- **Volume Surge Detection**: Detects significant spikes in 24h trading volume.
- **Resilient Startup**: Includes a Windows batch script (`run_bot.bat`) for automated environment activation and dependency management.
- **Secure Configuration**: All credentials and thresholds are managed via a `.env` file.
- **Professional Logging**: Clean console output for monitoring bot health.

## 🛠️ Setup Instructions

Follow these 3 steps to get the monitor running:

### 1. Environment Configuration
Create a `.env` file in the root directory and fill in your credentials:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
TOKEN_ADDRESS=solana_token_mint_address
```

### 2. Dependency Setup
Ensure you have Python installed. You don't need to manually install dependencies; the startup script handles it. However, for manual setup:
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Start Monitoring
Simply run the included batch script to activate the environment and start the bot:
```bash
./run_bot.bat
```

---
*Developed by Ghost Dev - Resilient Web3 Solutions.*

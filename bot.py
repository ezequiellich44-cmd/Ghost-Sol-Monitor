import asyncio
import os
import httpx
import logging
from dotenv import load_dotenv
from telegram import Bot

# Configuración de Logs para ver actividad en la consola
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TOKEN_ADDRESS = os.getenv("TOKEN_ADDRESS")


# Umbrales de Producción
PRICE_THRESHOLD = 5.0
VOLUME_THRESHOLD = 20.0
CHECK_INTERVAL = 300

class SolanaAlertBot:
    def __init__(self):
        self.bot = Bot(token=TOKEN)
        self.last_price = None
        self.last_volume = None
        self.client = httpx.AsyncClient(timeout=15.0)

    async def get_group_id_helper(self):
        """Detecta mensajes en Telegram y te grita el ID en la consola"""
        try:
            updates = await self.bot.get_updates(offset=-1, timeout=1)
            for u in updates:
                if u.message:
                    print(f"\n[RADAR] Mensaje en: {u.message.chat.title or 'Privado'}")
                    print(f"[RADAR] ID PARA TU .ENV: {u.message.chat.id}\n")
        except Exception:
            pass

    async def fetch_market_data(self):
        # Endpoint robusto para buscar por dirección de token
        url = f"https://api.dexscreener.com/latest/dex/tokens/{TOKEN_ADDRESS}"
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                data = response.json()
                return data['pairs'][0] if data.get('pairs') else None
        except Exception as e:
            logging.error(f"Error de red: {e}")
        return None

    async def send_telegram_alert(self, text):
        if not CHAT_ID: return
        try:
            await self.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')
        except Exception as e:
            logging.error(f"Error en Telegram: {e}")

    async def start(self):
        logging.info(f"--- Ghost Dev: Vigilancia Iniciada ({TOKEN_ADDRESS}) ---")
        
        while True:
            pair = await self.fetch_market_data()
            
            if pair:
                symbol = pair.get('baseToken', {}).get('symbol', 'TOKEN')
                price = float(pair.get('priceUsd', 0))
                volume = float(pair.get('volume', {}).get('h24', 0))
                logging.info(f"Escaneando {symbol}... Precio: ${price:.6f}")

                if self.last_price:
                    p_diff = ((price - self.last_price) / self.last_price) * 100
                    v_diff = ((volume - self.last_volume) / self.last_volume) * 100 if self.last_volume else 0
                    
                    if abs(p_diff) >= PRICE_THRESHOLD or v_diff >= VOLUME_THRESHOLD:
                        msg = f"<b>🚀 Alerta {symbol}</b>\n\n💰 Precio: ${price:.6f}\n📈 Cambio: {p_diff:+.4f}%"
                        msg += f"\n\n<a href='https://dexscreener.com/solana/{TOKEN_ADDRESS}'>🔗 Ver en DexScreener</a>"
                        await self.send_telegram_alert(msg)
                        logging.info(f"¡ALERTA ENVIADA!")

                self.last_price = price
                self.last_volume = volume
            else:
                logging.warning("Esperando datos de DexScreener... verifica el TOKEN_ADDRESS en tu .env")

            await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    bot = SolanaAlertBot()
    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        print("\nBot apagado.")
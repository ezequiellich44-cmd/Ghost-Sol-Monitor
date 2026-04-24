import asyncio
import os
import base58
import httpx
import logging
from dotenv import load_dotenv

from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.async_api import AsyncClient

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

# Lista de RPCs de Respaldo (Fallback)
FALLBACK_RPCS = [
    os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com"),
    "https://solana-mainnet.g.allnodes.com",
    "https://api.triton.one"
]

SOL_MINT = "So11111111111111111111111111111111111111112"

class GhostSniper:
    def __init__(self):
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key:
            raise ValueError("ERROR: PRIVATE_KEY no encontrada en .env")
        
        self.keypair = Keypair.from_base58_string(private_key)
        self.rpc_index = 0
        self.client = AsyncClient(FALLBACK_RPCS[self.rpc_index])
        self.http_client = httpx.AsyncClient(timeout=20.0, follow_redirects=True)
        logging.info(f"--- Sniper Inicializado: {self.keypair.pubkey()} ---")
        logging.info(f"--- RPC Primario: {FALLBACK_RPCS[self.rpc_index]} ---")

    async def switch_rpc(self):
        """Cambia al siguiente RPC en la lista si el actual falla"""
        self.rpc_index = (self.rpc_index + 1) % len(FALLBACK_RPCS)
        new_rpc = FALLBACK_RPCS[self.rpc_index]
        logging.warning(f"⚠️ Cambiando a RPC de respaldo: {new_rpc}")
        await self.client.close()
        self.client = AsyncClient(new_rpc)

    async def get_jupiter_quote(self, input_mint, output_mint, amount):
        """Paso 1: Obtener cotización de Jupiter V6"""
        url = f"https://quote-api.jup.ag/v6/quote?inputMint={input_mint}&outputMint={output_mint}&amount={amount}&slippageBps=50"
        
        try:
            response = await self.http_client.get(url)
            if response.status_code == 200:
                quote = response.json()
                logging.info(f"[QUOTE_FETCHED] Precio estimado: {quote.get('outAmount')}")
                return quote
            else:
                logging.error(f"Error en Quote API (Status {response.status_code}): {response.text}")
                return None
        except httpx.ConnectError:
            logging.error("❌ ERROR DE CONEXIÓN: No se pudo conectar con Jupiter API (DNS o Bloqueo).")
            return None
        except Exception as e:
            logging.error(f"Error inesperado en Quote: {e}")
            return None

    async def get_swap_transaction(self, quote):
        """Paso 2: Generar la transacción de Swap"""
        url = "https://quote-api.jup.ag/v6/swap"
        payload = {
            "quoteResponse": quote,
            "userPublicKey": str(self.keypair.pubkey()),
            "wrapAndUnwrapSol": True
        }
        
        try:
            response = await self.http_client.post(url, json=payload)
            if response.status_code == 200:
                tx_data = response.json()
                logging.info("[SWAP_TRANSACTION_READY] Transacción generada")
                return tx_data.get("swapTransaction")
            return None
        except Exception as e:
            logging.error(f"Error obteniendo transacción de swap: {e}")
            return None

    async def execute_swap(self, input_mint, output_mint, amount_sol):
        """Paso 3: Ciclo completo de ejecución con Reintento de RPC"""
        amount_lamports = int(amount_sol * 1_000_000_000)
        
        # 1. Cotizar
        quote = await self.get_jupiter_quote(input_mint, output_mint, amount_lamports)
        if not quote: return

        # 2. Obtener TX
        raw_tx = await self.get_swap_transaction(quote)
        if not raw_tx: return

        # 3. Firmar y Enviar (con reintento de RPC)
        for attempt in range(len(FALLBACK_RPCS)):
            try:
                tx_bytes = base58.b58decode(raw_tx)
                transaction = VersionedTransaction.from_bytes(tx_bytes)
                signature = self.keypair.sign_message(transaction.message)
                signed_tx = VersionedTransaction(transaction.message, [signature])

                logging.info(f"[SWAP_SIGNED] Enviando a {FALLBACK_RPCS[self.rpc_index]}...")
                res = await self.client.send_raw_transaction(bytes(signed_tx))
                logging.info(f"[TX_BROADCASTED] Signature: https://solscan.io/tx/{res.value}")
                return # Éxito
                
            except Exception as e:
                logging.error(f"Fallo en intento {attempt+1}: {e}")
                if attempt < len(FALLBACK_RPCS) - 1:
                    await self.switch_rpc()
                else:
                    logging.critical("🚨 Todos los RPCs han fallado.")

    async def close(self):
        await self.http_client.aclose()
        await self.client.close()

async def main():
    try:
        sniper = GhostSniper()
        USDC_MINT = "EPjFW36hd7T1nd6Xadgzgd7M7yH9Rgd6d8666M9G8FQf"
        
        print("\n--- INICIANDO PRUEBA DE DISPARO ---")
        await sniper.execute_swap(SOL_MINT, USDC_MINT, 0.001)
        await sniper.close()
    except Exception as e:
        logging.error(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
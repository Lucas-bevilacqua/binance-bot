import asyncio
import os
import pandas as pd
from binance import AsyncClient
import dotenv

dotenv.load_dotenv()

async def check():
    client = await AsyncClient.create(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_API_SECRET'))
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    for symbol in symbols:
        try:
            klines = await client.futures_klines(symbol=symbol, interval='15m', limit=100)
            df = pd.DataFrame(klines, columns=['ts', 'o', 'h', 'l', 'c', 'v', 'ct', 'qv', 't', 'tb', 'tq', 'i'])
            df['c'] = df['c'].astype(float)
            df['ema9'] = df['c'].ewm(span=9).mean()
            df['ema21'] = df['c'].ewm(span=21).mean()
            df['ema50'] = df['c'].ewm(span=50).mean()
            
            # Simple score check
            latest = df.iloc[-1]
            bull = 0
            bear = 0
            if latest['ema9'] > latest['ema21'] > latest['ema50']: bull += 25
            elif latest['ema9'] < latest['ema21'] < latest['ema50']: bear += 25
            
            print(f"{symbol}: Bull={bull}, Bear={bear}, Last={latest['c']}")
        except Exception as e:
            print(f"Error {symbol}: {e}")
    await client.close_connection()

if __name__ == '__main__':
    asyncio.run(check())

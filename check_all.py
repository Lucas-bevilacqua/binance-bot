import asyncio
import os
import pandas as pd
from binance import AsyncClient
import dotenv

dotenv.load_dotenv()

async def check():
    client = await AsyncClient.create()
    symbols = [
        'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT',
        'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT',
        'MATICUSDT', 'DOTUSDT', 'LINKUSDT', 'ATOMUSDT',
        'LTCUSDT', 'NEARUSDT', 'APTUSDT', 'ARBUSDT',
        'OPUSDT', 'INJUSDT', 'SUIUSDT', 'PEPEUSDT'
    ]
    for symbol in symbols:
        try:
            klines = await client.futures_klines(symbol=symbol, interval='15m', limit=100)
            df = pd.DataFrame(klines, columns=['ts', 'o', 'h', 'l', 'c', 'v', 'ct', 'qv', 't', 'tb', 'tq', 'i'])
            df['c'] = df['c'].astype(float)
            df['v'] = df['v'].astype(float)
            df['h'] = df['h'].astype(float)
            df['l'] = df['l'].astype(float)
            
            df['ema9'] = df['c'].ewm(span=9).mean()
            df['ema21'] = df['c'].ewm(span=21).mean()
            df['ema50'] = df['c'].ewm(span=50).mean()
            
            delta = df['c'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            df['ema12'] = df['c'].ewm(span=12).mean()
            df['ema26'] = df['c'].ewm(span=26).mean()
            df['macd'] = df['ema12'] - df['ema26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            
            df['bb_middle'] = df['c'].rolling(window=20).mean()
            df['bb_std'] = df['c'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
            df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
            
            latest = df.iloc[-1]
            bull = 0
            bear = 0
            
            if latest['ema9'] > latest['ema21'] > latest['ema50']: bull += 25
            elif latest['ema9'] < latest['ema21'] < latest['ema50']: bear += 25
            
            if latest['rsi'] < 30: bull += 20
            elif latest['rsi'] > 70: bear += 20
            
            macd_diff = latest['macd'] - latest['macd_signal']
            if macd_diff > 0: bull += 15
            else: bear += 15
            
            if latest['c'] < latest['bb_lower']: bull += 15
            elif latest['c'] > latest['bb_upper']: bear += 15
            
            vol_ma = df['v'].rolling(20).mean().iloc[-1]
            if latest['v'] > vol_ma * 1.5:
                bull += 10
                bear += 10
            
            trend = 'NEUTRAL'
            if bull > bear + 20: trend = 'LONG'
            elif bear > bull + 20: trend = 'SHORT'
            
            strength = max(bull, bear)
            print(f"{symbol:10} | Bull: {bull:2} | Bear: {bear:2} | Trend: {trend:7} | Strength: {strength:2}")
            
        except Exception as e:
            # print(f"Error {symbol}: {e}")
            pass
    await client.close_connection()

if __name__ == '__main__':
    asyncio.run(check())

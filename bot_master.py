#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 BOT AUTÔNOMO INTELIGENTE
===========================
Este bot:
1. Monitora o mercado 24/7
2. Decide quando ENTRAR baseado em análise técnica
3. Gerencia posições automaticamente
4. Decide quando SAIR (TP/SL)
5. Funciona 100% sozinho
"""

import asyncio
import os
import sys
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import numpy as np
from binance import AsyncClient
from colorama import Fore, Style, init
import dotenv
from openai import OpenAI

# Configurar UTF-8
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'detach'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

init(autoreset=True)
dotenv.load_dotenv()





class AutonomousBot:
    """Bot autônomo que toma decisões de trading sozinho."""

    def __init__(self):
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        self.openai_key = os.getenv('OPENAI_API_KEY')

        # Configurações de trading
        self.leverage = int(os.getenv('ALAVANCAGEM_PADRAO', 50))
        self.risk_per_trade = float(os.getenv('RISCO_MAXIMO_POR_OPERACAO', 0.12))
        self.tp_percent = float(os.getenv('TAKE_PROFIT_PERCENTUAL', 0.025))
        self.sl_percent = float(os.getenv('STOP_LOSS_PERCENTUAL', 0.015))

        # Configurações do bot
        self.scan_interval = int(os.getenv('SCAN_INTERVAL', 60))        # Escanear a cada X segundos
        self.monitor_interval = int(os.getenv('MONITOR_INTERVAL', 15))  # Monitorar a cada X segundos
        self.max_positions = int(os.getenv('MAX_POSITIONS', 3))         # Máximo de posições simultâneas
        self.min_signal_strength = int(os.getenv('MIN_SIGNAL_STRENGTH', 35)) # Força mínima para entrar

        # Pares monitorados (expandido para mais oportunidades)
        self.symbols = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT',
            'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT',
            'MATICUSDT', 'DOTUSDT', 'LINKUSDT', 'ATOMUSDT',
            'LTCUSDT', 'NEARUSDT', 'APTUSDT', 'ARBUSDT',
            'OPUSDT', 'INJUSDT', 'SUIUSDT', 'PEPEUSDT'
        ]

        # Posições ativas
        self.active_trades: Dict[str, Dict] = {}

        # Arquivos de dados
        self.dashboard_file = "dashboard_data.json"
        self.history_file = "trade_history.json"
        self.metrics_file = "daily_metrics.json"

        # Cliente OpenAI (opcional)
        self.ai_client = OpenAI(api_key=self.openai_key) if self.openai_key else None
        self.last_ai_analysis: Dict[str, Dict] = {}

        self.client = None
        self.running = True

    async def start(self):
        """Iniciar o bot autônomo."""
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}  🤖 BOT AUTÔNOMO INTELIGENTE")
        print(f"{Fore.CYAN}{'='*70}")
        print(f"{Fore.WHITE}  Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{Fore.WHITE}  Alavancagem: {self.leverage}x")
        print(f"{Fore.WHITE}  Risco por trade: {self.risk_per_trade*100:.1f}%")
        print(f"{Fore.WHITE}  Max posições: {self.max_positions}")
        print(f"{Fore.CYAN}{'='*70}\n")

        self.client = await AsyncClient.create(self.api_key, self.api_secret)

        # Variável para Watchdog
        self.last_heartbeat = datetime.now()

        try:
            # 0. Salvar estado inicial (para o dashboard não ficar vazio)
            self.save_dashboard_state()

            # 1. Sincronização Retroativa de Histórico
            await self.sync_historical_trades()

            # 1. Sincronizar posições existentes
            await self.sync_open_positions()
            
            # Loop principal
            while self.running:
                # Atualizar batimento cardíaco
                self.last_heartbeat = datetime.now()

                try:
                    # 1. Monitorar posições abertas
                    await self.monitor_positions()

                    # 2. Salvar estado para o Dashboard
                    self.save_dashboard_state()

                    # 2. Escanear novas oportunidades
                    open_pos_count = len(self.active_trades)

                    if open_pos_count < self.max_positions:
                        print(f"{Fore.CYAN}[{self.now()}] Buscando oportunidades... ({open_pos_count}/{self.max_positions} posições)")

                        opportunity = await self.find_best_opportunity()

                        if opportunity:
                            print(f"{Fore.GREEN}[{self.now()}] ⚡ Oportunidade: {opportunity['symbol']} {opportunity['trend']} (Força: {opportunity['strength']})")

                            # Confirmar e entrar
                            success = await self.enter_trade(opportunity)

                            if success:
                                open_pos_count += 1
                        else:
                            print(f"{Fore.YELLOW}[{self.now()}] Nenhuma oportunidade de qualidade")
                    else:
                        print(f"{Fore.WHITE}[{self.now()}] Máximo de posições atingido")

                    # 3. Aguardar próximo ciclo
                    print(f"{Fore.WHITE}[{self.now()}] Aguardando {self.monitor_interval}s...\n")
                    await asyncio.sleep(self.monitor_interval)

                except Exception as e:
                    print(f"{Fore.RED}[{self.now()}] Erro no loop: {e}")
                    await asyncio.sleep(10)

        finally:
            await self.client.close_connection()

    async def monitor_positions(self):
        """Monitora posições abertas (com proteção dupla: exchange + local)."""
        try:
            # Obter posições da Binance
            positions = await self.client.futures_position_information()
            open_positions = {p['symbol']: p for p in positions if float(p['positionAmt']) != 0}

            # 0. Sincronizar posições externas (Manuais ou Nuvem)
            for symbol, pos in open_positions.items():
                if symbol in self.symbols and symbol not in self.active_trades:
                    print(f"{Fore.YELLOW}[{self.now()}] ⚠️ Posição externa detectada: {symbol}. Importando...")
                    
                    entry_price = float(pos['entryPrice'])
                    quantity = abs(float(pos['positionAmt']))
                    side = 'LONG' if float(pos['positionAmt']) > 0 else 'SHORT'
                    
                    # Adicionar à memória do bot
                    self.active_trades[symbol] = {
                        'side': side,
                        'entry': entry_price,
                        'quantity': quantity,
                        'sl': 0.0, # Será corrigido pelo Auto-Heal
                        'tp': 0.0, # Será corrigido pelo Auto-Heal
                        'entry_time': self.now(),
                        'sl_order_id': None,
                        'tp_order_id': None
                    }

            # Verificar cada posição ativa no bot
            for symbol, trade in list(self.active_trades.items()):
                if symbol not in open_positions:
                    # Posição foi fechada (por SL/TP ou manualmente)
                    print(f"{Fore.YELLOW}[{self.now()}] {symbol} - Posição fechada (SL/TP atingido ou fechamento manual)")
                    
                    # Gravar resultado no histórico antes de deletar
                    await self._record_trade_result(symbol, trade['side'], trade['entry'], trade['quantity'])
                    
                    # Cancelar ordens pendentes se existirem
                    try:
                        await self.client.futures_cancel_all_open_orders(symbol=symbol)
                    except:
                        pass
                    
                    del self.active_trades[symbol]
                    continue

                # Atualizar PnL
                pos = open_positions[symbol]
                current_pnl = float(pos['unRealizedProfit'])
                current_price = float(pos['markPrice'])

                # Calcular ROE
                entry_price = float(pos['entryPrice'])
                notional = abs(float(pos['positionAmt']) * entry_price)
                roe = (current_pnl / notional * 100) if notional > 0 else 0

                # Verificar status das ordens SL/TP
                sl_status = "✅" if trade.get('sl_order_id') else "❌"
                tp_status = "✅" if trade.get('tp_order_id') else "❌"

                # Se não tem ordens na exchange, tentar AUTO-HEAL
                if not trade.get('sl_order_id') or not trade.get('tp_order_id'):
                    # Tentar corrigir orders
                    sl_oid = trade.get('sl_order_id')
                    tp_oid = trade.get('tp_order_id')
                    quantity = trade['quantity']
                    
                    # Recuperar objetos de ordem parciais para passar para funçao
                    sl_ord = {'orderId': sl_oid, 'stopPrice': trade['sl']} if sl_oid else None
                    tp_ord = {'orderId': tp_oid, 'price': trade['tp']} if tp_oid else None
                    
                    await self._auto_heal_position(symbol, trade['side'], trade['entry'], quantity, sl_ord, tp_ord)

                    # Verificar se corrigiu (apenas update visual, o proximo loop atualiza status real)
                    if not sl_oid or not tp_oid:
                        # Se ainda assim falhar, fazer monitoramento local
                        # Verificar Stop Loss (local)
                        if trade['side'] == 'LONG':
                            sl_hit = current_price <= trade['sl']
                            tp_hit = current_price >= trade['tp']
                        else:  # SHORT
                            sl_hit = current_price >= trade['sl']
                            tp_hit = current_price <= trade['tp']

                        # SAIR se hit TP ou SL
                        if sl_hit:
                            print(f"{Fore.RED}[{self.now()}] {symbol} - STOP LOSS HIT! Fechando...")
                            await self.close_position(symbol)
                            continue

                        if tp_hit:
                            print(f"{Fore.GREEN}[{self.now()}] {symbol} - TAKE PROFIT HIT! Fechando...")
                            await self.close_position(symbol)
                            continue

                # Mostrar status
                pnl_color = Fore.GREEN if current_pnl > 0 else Fore.RED
                print(f"{pnl_color}[{self.now()}] {symbol} {trade['side']} | "
                      f"PnL: ${current_pnl:.4f} ({roe:+.2f}%) | "
                      f"Price: ${current_price:.4f} | "
                      f"SL{sl_status} TP{tp_status}")

                # Atualizar no dicionário
                trade['current_pnl'] = current_pnl
                trade['current_price'] = current_price
                trade['current_pnl_percent'] = roe

        except Exception as e:
            print(f"{Fore.RED}Erro ao monitorar: {e}")

    async def analyze_market_with_ai(self, symbol: str, signal_data: Dict) -> Dict:
        """Usa OpenAI para filtrar o sinal técnico."""
        if not self.ai_client:
            return {"decision": "GO", "reason": "IA não configurada (faltando chave)"}

        print(f"{Fore.CYAN}[{self.now()}] 🧠 Consultando IA para {symbol}...")
        
        try:
            signals = signal_data.get('signals', {})
            history = signal_data.get('history', [])
            
            history_str = "\n".join([f"- Preço: ${h['price']}, Vol: {h['vol']}" for h in history])

            prompt = f"""
            Você é um "Scalper Agressivo de Alta Frequência" especialista em capturar pequenos movimentos rápidos (scalping) em criptomoedas.
            
            Analise o cenário para {symbol} e decida se entramos para um trade rápido.
            
            DADOS TÉCNICOS:
            - Tendência: {signal_data['trend']}
            - Preço: ${signal_data.get('entry')}
            - RSI: {signals.get('rsi'):.2f} (Alvo: Scalping aceita RSI até 75 para LONG ou 25 para SHORT)
            - MACD: {signals.get('macd'):.6f}
            - Volume: {signals.get('rel_volume'):.2f}x (0.5x+ já é aceitável se a tendência for forte)
            
            REGRAS DE DECISÃO:
            1. Seja menos rígido: Se a tendência (EMA) for clara, ignore se o volume estiver um pouco baixo.
            2. Não tenha medo de "comprar o topo" se o momentum for forte.
            3. Responda APENAS em JSON.
            
            JSON FORMAT:
            {{
                "decision": "GO" ou "NO-GO",
                "sentiment": 0-100,
                "reason": "Explicação curta e agressiva"
            }}
            """

            response = self.ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={ "type": "json_object" }
            )

            import json
            result = json.loads(response.choices[0].message.content)
            
            # Guardar para o dashboard e cooldown
            self.last_ai_analysis[symbol] = {
                "decision": result.get('decision'),
                "sentiment": result.get('sentiment'),
                "reason": result.get('reason'),
                "time": self.now(),
                "timestamp": datetime.now() # Usado para controle interno de cooldown
            }
            
            return result

        except Exception as e:
            print(f"{Fore.RED}[{self.now()}] Erro na análise de IA: {e}")
            return {"decision": "GO", "reason": f"Erro na IA ({e}), seguindo sinal técnico."}

    async def find_best_opportunity(self) -> Optional[Dict]:
        """Encontra a melhor oportunidade de entrada."""
        best_opportunity = None
        best_score = 0

        for symbol in self.symbols:
            # Não abrir se já tem posição
            if symbol in self.active_trades:
                continue

            try:
                analysis = await self.analyze_symbol(symbol)

                if analysis['strength'] >= self.min_signal_strength and analysis['trend'] != 'NEUTRAL':
                    # FILTRO DE IA (Opcional se configurado)
                    if self.ai_client:
                        # 🧠 Lógica de Cooldown para evitar gastos excessivos
                        last_ai = self.last_ai_analysis.get(symbol)
                        if last_ai and last_ai.get('decision') == 'NO-GO':
                            time_diff = datetime.now() - last_ai.get('timestamp', datetime.min)
                            if time_diff.total_seconds() < 600: # 10 minutos de "castigo" para a moeda
                                # Pular sem chamar a API de novo
                                continue

                        ai_result = await self.analyze_market_with_ai(symbol, analysis)
                        if ai_result.get('decision') == 'NO-GO':
                            print(f"{Fore.YELLOW}[{self.now()}] 🧠 IA bloqueou entrada em {symbol}: {ai_result.get('reason')}")
                            continue
                        else:
                            print(f"{Fore.CYAN}[{self.now()}] 🧠 IA validou entrada em {symbol}: {ai_result.get('reason')}")
                    
                    if analysis['strength'] > best_score:
                        best_score = analysis['strength']
                        best_opportunity = analysis

            except Exception as e:
                continue

        return best_opportunity

    async def analyze_symbol(self, symbol: str) -> Dict:
        """Analisa um par e retorna sinal."""
        try:
            klines = await self.client.futures_klines(symbol=symbol, interval='15m', limit=100)
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            df['close'] = df['close'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['volume'] = df['volume'].astype(float)

            # Indicadores
            df['ema_9'] = df['close'].ewm(span=9).mean()
            df['ema_21'] = df['close'].ewm(span=21).mean()
            df['ema_50'] = df['close'].ewm(span=50).mean()

            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

            # MACD
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()

            # Bollinger
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            df['bb_std'] = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
            df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)

            latest = df.iloc[-1]

            # Calcular score
            bullish_score = 0
            bearish_score = 0

            if latest['ema_9'] > latest['ema_21'] > latest['ema_50']:
                bullish_score += 25
            elif latest['ema_9'] < latest['ema_21'] < latest['ema_50']:
                bearish_score += 25

            if latest['rsi'] < 30:
                bullish_score += 20
            elif latest['rsi'] > 70:
                bearish_score += 20

            macd_diff = latest['macd'] - latest['macd_signal']
            if macd_diff > 0:
                bullish_score += 15
            else:
                bearish_score += 15

            if latest['close'] < latest['bb_lower']:
                bullish_score += 15
            elif latest['close'] > latest['bb_upper']:
                bearish_score += 15

            # Volume
            vol_ma = df['volume'].rolling(20).mean().iloc[-1]
            relative_volume = latest['volume'] / vol_ma if vol_ma > 0 else 1.0
            
            if relative_volume > 1.5:
                bullish_score += 10
                bearish_score += 10

            trend = 'NEUTRAL'
            strength = max(bullish_score, bearish_score)

            if bullish_score > bearish_score + 10:
                trend = 'LONG'
            elif bearish_score > bullish_score + 10:
                trend = 'SHORT'

            entry_price = latest['close']
            atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]

            if trend == 'LONG':
                sl = entry_price - (atr * 1.5)
                tp = entry_price + (atr * 3)
            elif trend == 'SHORT':
                sl = entry_price + (atr * 1.5)
                tp = entry_price - (atr * 3)
            else:
                sl = tp = entry_price

            # Histórico recente (últimos 5 candles)
            recent_history = []
            for i in range(-5, 0):
                try:
                    row = df.iloc[i]
                    recent_history.append({
                        "price": round(row['close'], 4),
                        "vol": round(row['volume'], 2)
                    })
                except: pass

            return {
                'symbol': symbol,
                'trend': trend,
                'strength': strength,
                'entry': entry_price,
                'sl': sl,
                'tp': tp,
                'signals': {
                    'ema_9': latest['ema_9'],
                    'ema_21': latest['ema_21'],
                    'ema_50': latest['ema_50'],
                    'rsi': latest['rsi'],
                    'macd': macd_diff,
                    'bb_upper': latest['bb_upper'],
                    'bb_lower': latest['bb_lower'],
                    'rel_volume': relative_volume
                },
                'history': recent_history
            }

        except Exception as e:
            return {'symbol': symbol, 'trend': 'NEUTRAL', 'strength': 0}

    async def _check_min_notional(self, symbol: str, quantity: float, price: float) -> bool:
        """Verifica se o valor da ordem atende o mínimo exigido pela Binance."""
        try:
            info = await self.client.futures_exchange_info()
            symbol_info = next(s for s in info['symbols'] if s['symbol'] == symbol)
            min_notional_filter = next((f for f in symbol_info['filters'] if f['filterType'] == 'MIN_NOTIONAL'), None)
            
            if min_notional_filter:
                min_notional = float(min_notional_filter['notional'])
                if quantity * price < min_notional:
                    print(f"{Fore.YELLOW}[{self.now()}] ⚠️ Ordem muito pequena: ${quantity * price:.2f} < Min ${min_notional}")
                    return False
            return True
        except Exception:
            return True  # Se falhar a verificação, tenta enviar mesmo assim

    async def sync_open_positions(self):
        """Sincroniza posições já abertas na Binance e aplica SL/TP se faltar (Auto-Heal)."""
        print(f"{Fore.CYAN}[{self.now()}] 🔄 Sincronizando posições existentes...")
        try:
            positions = await self.client.futures_position_information()
            active_positions = [p for p in positions if float(p['positionAmt']) != 0]

            for pos in active_positions:
                symbol = pos['symbol']
                
                # Se já está rastreando, ignora
                if symbol in self.active_trades:
                    continue

                if symbol not in self.symbols:
                    print(f"{Fore.YELLOW}[{self.now()}] ⚠️ Encontrado {symbol} aberto, mas não está na lista de monitoramento. Ignorando.")
                    continue

                entry_price = float(pos['entryPrice'])
                amt = float(pos['positionAmt'])
                side = 'LONG' if amt > 0 else 'SHORT'
                quantity = abs(amt)
                
                # Tentar recuperar SL/TP das ordens abertas
                orders = await self.client.futures_get_open_orders(symbol=symbol)
                sl_order = next((o for o in orders if o['type'] in ['STOP_MARKET', 'STOP']), None)
                tp_order = next((o for o in orders if o['type'] in ['TAKE_PROFIT_MARKET', 'TAKE_PROFIT', 'LIMIT'] and o.get('reduceOnly')), None)

                # Auto-Heal: Se não tiver SL ou TP, tentar corrigir
                if not sl_order or not tp_order:
                    await self._auto_heal_position(symbol, side, entry_price, quantity, sl_order, tp_order)
                    # Recarregar ordens após tentativa de heal
                    orders = await self.client.futures_get_open_orders(symbol=symbol)
                    sl_order = next((o for o in orders if o['type'] in ['STOP_MARKET', 'STOP']), None)
                    tp_order = next((o for o in orders if o['type'] in ['TAKE_PROFIT_MARKET', 'TAKE_PROFIT', 'LIMIT'] and o.get('reduceOnly')), None)

                # Definir preços finais (existentes ou calculados)
                current_sl_price = float(sl_order['stopPrice']) if sl_order else 0.0
                current_tp_price = float(tp_order['price']) if tp_order else 0.0

                self.active_trades[symbol] = {
                    'side': side,
                    'entry': entry_price,
                    'sl': current_sl_price,
                    'tp': current_tp_price,
                    'quantity': quantity,
                    'order_id': 'SYNCED',
                    'sl_order_id': sl_order['orderId'] if sl_order else None,
                    'tp_order_id': tp_order['orderId'] if tp_order else None,
                    'entry_time': datetime.now()
                }
                print(f"{Fore.GREEN}[{self.now()}] ✅ Posição sincronizada: {symbol} {side} | Entry ${entry_price:.4f}")

        except Exception as e:
            print(f"{Fore.RED}[{self.now()}] ❌ Erro ao sincronizar: {e}")

    async def _auto_heal_position(self, symbol, side, entry_price, quantity, sl_order, tp_order):
        """Tenta colocar SL/TP em posições desprotegidas."""
        print(f"{Fore.YELLOW}[{self.now()}] 🚑 Auto-Healing {symbol}: Faltando SL/TP. Calculando...")
        try:
            # Calcular ATR para definir níveis
            klines = await self.client.futures_klines(symbol=symbol, interval='15m', limit=100)
            df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'ct', 'qv', 'tr', 'tb', 'tq', 'ig'])
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]

            # Obter precisão de preço
            info = await self.client.futures_exchange_info()
            symbol_info = next(s for s in info['symbols'] if s['symbol'] == symbol)
            price_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER')
            tick_size = float(price_filter['tickSize'])
            price_precision = len(str(tick_size).rstrip('0').split('.')[-1]) if '.' in str(tick_size) else 0

            # Calcular níveis
            if side == 'LONG':
                calculated_sl = entry_price - (atr * 1.5)
                calculated_tp = entry_price + (atr * 3)
            else:
                calculated_sl = entry_price + (atr * 1.5)
                calculated_tp = entry_price - (atr * 3)
            
            calculated_sl = round(calculated_sl, price_precision)
            calculated_tp = round(calculated_tp, price_precision)

            # Colocar SL se faltar
            if not sl_order:
                sl_side = 'SELL' if side == 'LONG' else 'BUY'
                try:
                    sl_order_obj = await self.client.futures_create_order(
                        symbol=symbol,
                        side=sl_side,
                        type='STOP_MARKET',
                        stopPrice=calculated_sl,
                        closePosition=True,
                        workingType='MARK_PRICE',
                        priceProtect=True
                    )
                    print(f"{Fore.YELLOW}[{self.now()}] 🛡️  Auto-SL colocado: ${calculated_sl}")
                except Exception as e:
                    print(f"{Fore.RED}[{self.now()}] Falha ao colocar Auto-SL: {e}")

            # Colocar TP se faltar
            if not tp_order:
                tp_side = 'SELL' if side == 'LONG' else 'BUY'
                try:
                    tp_order_obj = await self.client.futures_create_order(
                        symbol=symbol,
                        side=tp_side,
                        type='LIMIT',
                        quantity=quantity,
                        price=calculated_tp,
                        timeInForce='GTC',
                        reduceOnly=True
                    )
                    print(f"{Fore.GREEN}[{self.now()}] 🎯 Auto-TP colocado: ${calculated_tp}")
                except Exception as e:
                    print(f"{Fore.RED}[{self.now()}] Falha ao colocar Auto-TP: {e}")
                    
        except Exception as e:
            print(f"{Fore.RED}[{self.now()}] Erro no cálculo de Auto-Heal: {e}")

    async def enter_trade(self, opp: Dict) -> bool:
        """Entra em uma operação com SL/TP reais na exchange (Robusto)."""
        try:
            symbol = opp['symbol']
            side = 'BUY' if opp['trend'] == 'LONG' else 'SELL'

            # Obter informações do símbolo e filtros
            info = await self.client.futures_exchange_info()
            symbol_info = next(s for s in info['symbols'] if s['symbol'] == symbol)
            
            # Filtros de quantidade
            lot_size = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
            step_size = float(lot_size['stepSize'])
            qty_precision = len(str(step_size).rstrip('0').split('.')[-1]) if '.' in str(step_size) else 0

            # Filtros de preço
            price_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'PRICE_FILTER')
            tick_size = float(price_filter['tickSize'])
            price_precision = len(str(tick_size).rstrip('0').split('.')[-1]) if '.' in str(tick_size) else 0

            # Obter saldo e calcular quantidade
            account = await self.client.futures_account()
            balance = float(account['totalWalletBalance'])
            
            risk_amount = balance * self.risk_per_trade
            entry_price = opp['entry']
            quantity = (risk_amount * self.leverage) / entry_price
            quantity = round(quantity, qty_precision)

            # Validar Notional Mínimo (Evita erro -4164)
            if not await self._check_min_notional(symbol, quantity, entry_price):
                print(f"{Fore.YELLOW}[{self.now()}] ⚠️ Ajustando quantidade para mínimo notional...")
                # Tenta aumentar para o mínimo (simples: 2x o risco ou $6 USD)
                quantity = round(6.0 / entry_price, qty_precision) 

            # Configurar alavancagem
            await self.client.futures_change_leverage(symbol=symbol, leverage=self.leverage)

            # Preços SL/TP arredondados
            sl_price = round(opp['sl'], price_precision)
            tp_price = round(opp['tp'], price_precision)

            # 1. Executar ordem de entrada
            order = await self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            print(f"{Fore.GREEN}[{self.now()}] ✅ Ordem executada: {symbol} {side} | Obj: {quantity} | ID: {order['orderId']}")

            # Aguardar confirmação e obter preço real de entrada
            await asyncio.sleep(2)
            position = await self.client.futures_position_information(symbol=symbol)
            real_entry = float(position[0]['entryPrice'])

            # 2. Colocar STOP LOSS (com Retry e Fallback)
            sl_side = 'SELL' if side == 'BUY' else 'BUY'
            sl_order_id = None
            
            for attempt in range(3): # Tenta 3 vezes
                try:
                    # Tenta STOP_MARKET primeiro
                    sl_order = await self.client.futures_create_order(
                        symbol=symbol,
                        side=sl_side,
                        type='STOP_MARKET',
                        stopPrice=sl_price,
                        closePosition=True,
                        workingType='MARK_PRICE',
                        priceProtect=True
                    )
                    sl_order_id = sl_order['orderId']
                    print(f"{Fore.YELLOW}[{self.now()}] 🛡️  Stop Loss (Market) colocado: ${sl_price:.4f}")
                    break
                except Exception as e:
                    # Fallback: Tenta STOP LIMIT se Market falhar (Erro -4012)
                    if "Order type not supported" in str(e) or attempt == 2:
                        try:
                            # Preço limite um pouco pior para garantir execução
                            limit_price = sl_price * (0.999 if sl_side == 'SELL' else 1.001)
                            limit_price = round(limit_price, price_precision)
                            
                            sl_order = await self.client.futures_create_order(
                                symbol=symbol,
                                side=sl_side,
                                type='STOP',
                                quantity=quantity,
                                price=limit_price,
                                stopPrice=sl_price,
                                timeInForce='GTC'
                            )
                            sl_order_id = sl_order['orderId']
                            print(f"{Fore.YELLOW}[{self.now()}] 🛡️  Stop Loss (Limit) colocado: ${sl_price:.4f}")
                            break
                        except Exception as e2:
                            print(f"{Fore.RED}[{self.now()}] ⚠️ Falha fallback SL: {e2}")
                    
                    await asyncio.sleep(1)

            if not sl_order_id:
                print(f"{Fore.CYAN}[{self.now()}] 📡 Usando monitoramento local para SL")

            # 3. Colocar TAKE PROFIT (LIMIT reduceOnly)
            tp_side = 'SELL' if side == 'BUY' else 'BUY'
            tp_order_id = None
            
            for attempt in range(3):
                try:
                    tp_order = await self.client.futures_create_order(
                        symbol=symbol,
                        side=tp_side,
                        type='LIMIT',
                        quantity=quantity,
                        price=tp_price,
                        timeInForce='GTC',
                        reduceOnly=True
                    )
                    tp_order_id = tp_order['orderId']
                    print(f"{Fore.GREEN}[{self.now()}] 🎯 Take Profit (Limit) colocado: ${tp_price:.4f}")
                    break
                except Exception as e:
                    print(f"{Fore.YELLOW}[{self.now()}] ⚠️ TP falhou (tentativa {attempt+1}): {e}")
                    await asyncio.sleep(2) # Espera posição confirmar
            
            if not tp_order_id:
                print(f"{Fore.CYAN}[{self.now()}] 📡 Usando monitoramento local para TP")

            # Guardar informações
            self.active_trades[symbol] = {
                'side': opp['trend'],
                'entry': real_entry,
                'sl': sl_price,
                'tp': tp_price,
                'quantity': quantity,
                'order_id': order['orderId'],
                'sl_order_id': sl_order_id,
                'tp_order_id': tp_order_id,
                'entry_time': datetime.now()
            }
            
            return True

        except Exception as e:
            print(f"{Fore.RED}[{self.now()}] ❌ Erro crítico ao entrar: {e}")
            return False

    async def sync_historical_trades(self, days=7):
        """Busca trades passados na Binance e reconstrói o histórico local."""
        print(f"{Fore.CYAN}[{self.now()}] 🕰️ Sincronizando histórico dos últimos {days} dias...")
        try:
            import json
            import time
            start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
            
            all_historical_records = []
            
            for symbol in self.symbols:
                # Buscar trades do par
                trades = await self.client.futures_account_trades(symbol=symbol, startTime=start_time)
                if not trades:
                    continue

                # Agrupar trades por Realized PnL (cada fechamento gera um PnL realizado)
                for t in trades:
                    pnl = float(t.get('realizedPnl', 0))
                    if pnl != 0:
                        # Criar um registro de histórico a partir do trade de fechamento
                        dt_obj = datetime.fromtimestamp(t['time'] / 1000)
                        all_historical_records.append({
                            "symbol": symbol,
                            "side": "SELL" if float(t['qty']) < 0 else "BUY", # Simplificado: lado da ordem de FECHAMENTO
                            "entry": 0.0, # Binance não fornece a entrada original no trade de saída facilmente
                            "exit": float(t['price']),
                            "quantity": abs(float(t['qty'])),
                            "pnl": pnl,
                            "time": dt_obj.strftime('%Y-%m-%d %H:%M:%S')
                        })

            if not all_historical_records:
                print(f"{Fore.YELLOW}[{self.now()}] Nenhum trade passado encontrado.")
                return

            # Ordenar por tempo
            all_historical_records.sort(key=lambda x: x['time'])

            # Salvar no arquivo de histórico (sem duplicatas)
            existing_history = []
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    existing_history = json.load(f)
            
            # Unificar (baseado em symbol + pnl + time)
            history_keys = {f"{r['symbol']}_{r['pnl']}_{r['time']}" for r in existing_history}
            for r in all_historical_records:
                key = f"{r['symbol']}_{r['pnl']}_{r['time']}"
                if key not in history_keys:
                    existing_history.append(r)
            
            existing_history.sort(key=lambda x: x['time'])
            with open(self.history_file, 'w') as f:
                json.dump(existing_history[-100:], f, indent=4)

            # Reconstruir métricas diárias
            daily_stats = {}
            for r in existing_history:
                day = r['time'].split(' ')[0]
                if day not in daily_stats:
                    daily_stats[day] = {"date": day, "pnl": 0.0, "trades": 0}
                daily_stats[day]['pnl'] += r['pnl']
                daily_stats[day]['trades'] += 1
            
            metrics = sorted(list(daily_stats.values()), key=lambda x: x['date'])
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics, f, indent=4)

            print(f"{Fore.GREEN}[{self.now()}] ✅ Histórico sincronizado: {len(all_historical_records)} trades processados.")

        except Exception as e:
            print(f"{Fore.RED}[{self.now()}] Erro na sincronização retroativa: {e}")

    async def _record_trade_result(self, symbol, side, entry, quantity):
        """Busca o resultado real do trade na Binance e grava no histórico."""
        try:
            # Pegar o último trade fechado para este símbolo
            trades = await self.client.futures_account_trades(symbol=symbol, limit=5)
            if not trades:
                return

            # Calcular lucro total das últimas transações de fechamento
            realized_pnl = 0.0
            last_price = 0.0
            for t in reversed(trades):
                # Se for um trade de fechamento (realizedPnl != 0)
                pnl = float(t.get('realizedPnl', 0))
                if pnl != 0:
                    realized_pnl += pnl
                    last_price = float(t['price'])
                    break # Pegamos o último fechamento

            if realized_pnl == 0:
                return

            # Gravar no histórico
            import json
            history = []
            if os.path.exists(self.history_file):
                try:
                    with open(self.history_file, 'r') as f:
                        history = json.load(f)
                except: history = []
            
            new_record = {
                "symbol": symbol,
                "side": side,
                "entry": entry,
                "exit": last_price,
                "quantity": quantity,
                "pnl": realized_pnl,
                "time": self.now()
            }
            history.append(new_record)
            history = history[-100:] # Manter 100
            
            with open(self.history_file, 'w') as f:
                json.dump(history, f, indent=4)
                
            # Atualizar métricas diárias
            await self._update_daily_metrics(realized_pnl)
            
        except Exception as e:
            print(f"{Fore.RED}[{self.now()}] Erro ao gravar histórico: {e}")

    async def _update_daily_metrics(self, pnl):
        """Atualiza métricas diárias de performance."""
        try:
            import json
            metrics = []
            today = datetime.now().strftime('%Y-%m-%d')
            
            if os.path.exists(self.metrics_file):
                try:
                    with open(self.metrics_file, 'r') as f:
                        metrics = json.load(f)
                except: metrics = []
            
            found = False
            for m in metrics:
                if m['date'] == today:
                    m['pnl'] = m.get('pnl', 0) + pnl
                    m['trades'] = m.get('trades', 0) + 1
                    found = True
                    break
            
            if not found:
                metrics.append({"date": today, "pnl": pnl, "trades": 1})
            
            metrics = metrics[-30:] # Últimos 30 dias
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics, f, indent=4)
        except Exception as e:
            print(f"{Fore.RED}[{self.now()}] Erro nas métricas diárias: {e}")

    def save_dashboard_state(self):
        """Salva o estado atual do bot para o dashboard."""
        try:
            import json
            # Carregar histórico e métricas para enviar ao dashboard
            history = []
            if os.path.exists(self.history_file):
                try:
                    with open(self.history_file, 'r') as f:
                        history = json.load(f)
                except: pass
            
            metrics = []
            if os.path.exists(self.metrics_file):
                try:
                    with open(self.metrics_file, 'r') as f:
                        metrics = json.load(f)
                except: pass

            # Converter objetos datetime para string para serialização JSON
            active_trades_serializable = {}
            for symbol, trade in self.active_trades.items():
                trade_copy = trade.copy()
                if isinstance(trade_copy.get('entry_time'), datetime):
                    trade_copy['entry_time'] = trade_copy['entry_time'].strftime('%Y-%m-%d %H:%M:%S')
                active_trades_serializable[symbol] = trade_copy

            # Converter análises de IA para serializável (remover timestamp)
            ai_analysis_serializable = {}
            for sym, data_ai in self.last_ai_analysis.items():
                data_copy = data_ai.copy()
                if 'timestamp' in data_copy: del data_copy['timestamp']
                ai_analysis_serializable[sym] = data_copy

            state = {
                "active_trades": active_trades_serializable,
                "history": history[-50:], # Últimos 50 para o dashboard
                "daily_metrics": metrics,
                "ai_analysis": ai_analysis_serializable,
                "symbols": self.symbols,
                "last_update": self.now(),
                "config": {
                    "leverage": self.leverage,
                    "max_positions": self.max_positions,
                    "risk": self.risk_per_trade,
                    "min_signal": self.min_signal_strength
                }
            }
            # Salvar de forma atômica (temporário -> final)
            temp_file = self.dashboard_file + ".tmp"
            with open(temp_file, 'w') as f:
                json.dump(state, f, indent=4)
            os.replace(temp_file, self.dashboard_file)
        except Exception as e:
            print(f"{Fore.RED}[{self.now()}] Erro ao salvar estado do dashboard: {e}")

    async def close_position(self, symbol: str):
        """Fecha uma posição."""
        try:
            positions = await self.client.futures_position_information(symbol=symbol)
            pos_amt = float(positions[0]['positionAmt'])

            if abs(pos_amt) == 0:
                del self.active_trades[symbol]
                return

            side = 'SELL' if pos_amt > 0 else 'BUY'

            # Cancelar ordens
            await self.client.futures_cancel_all_open_orders(symbol=symbol)

            # Fechar posição
            order = await self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=abs(pos_amt),
                reduceOnly='true'
            )

            print(f"{Fore.GREEN}[{self.now()}] ✅ {symbol} fechada")

            # Remover do dicionário
            if symbol in self.active_trades:
                del self.active_trades[symbol]

        except Exception as e:
            print(f"{Fore.RED}[{self.now()}] ❌ Erro ao fechar {symbol}: {e}")

    @staticmethod
    def now():
        return datetime.now().strftime('%H:%M:%S')


async def main():
    """Função principal."""
    try:
        bot = AutonomousBot()
        await bot.start()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Bot encerrado pelo usuário")


if __name__ == "__main__":
    asyncio.run(main())

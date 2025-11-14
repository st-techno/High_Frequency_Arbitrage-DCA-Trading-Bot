"""
BitMEX-Binance BTC Perpetual Arbitrage & DCA Bot with Redis, Prometheus, WebSocket
Author: ST Technologies 
Copyright @ ST Technologies
"""

import ccxt
import asyncio
import aioredis
import json
import logging
import prometheus_client
from prometheus_client import Gauge, start_http_server
import websockets
import numpy as np
from datetime import datetime

# ==== CONFIGURATION ====

CONFIG = {
    "bitmex_api_key": "YOUR_BITMEX_KEY",
    "bitmex_api_secret": "YOUR_BITMEX_SECRET",
    "binance_api_key": "YOUR_BINANCE_KEY",
    "binance_api_secret": "YOUR_BINANCE_SECRET",
    "symbol_bitmex": "BTC/USDT:USDT",
    "symbol_binance": "BTC/USDT",
    "leverage": 3,
    "funding_threshold": 0.0007,
    "dca_step_pct": 1.2,
    "max_dca_levels": 6,
    "risk_limit": 0.15,
    "redis_url": "redis://localhost",
    "prometheus_port": 8000,
    "websocket_uri_binance": "wss://stream.binance.com:9443/ws/btcusdt@ticker",
    "websocket_uri_bitmex": "wss://www.bitmex.com/realtime?subscribe=instrument:XBTUSDT"
}

# ==== LOGGING ====

logging.basicConfig(
    filename='bitmex_binance_dca_redis.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

# ==== PROMETHEUS METRICS ====

funding_diff_gauge = Gauge('funding_rate_difference', 'Difference between BitMEX and Binance funding rates')
spread_gauge = Gauge('price_spread', 'Price Spread between BitMEX and Binance BTC/USDT')
executed_trades_gauge = Gauge('executed_trades', 'Number of executed arbitrage trades')

# ==== EXCHANGE INITIALIZATION ====

def init_exchanges():
    bitmex = ccxt.bitmex({
        'apiKey': CONFIG['bitmex_api_key'],
        'secret': CONFIG['bitmex_api_secret'],
        'enableRateLimit': True,
        'urls': {'api': 'https://www.bitmex.com'}
    })
    binance = ccxt.binance({
        'apiKey': CONFIG['binance_api_key'],
        'secret': CONFIG['binance_api_secret'],
        'enableRateLimit': True,
        'options': {'defaultType': 'future'},
    })
    return bitmex, binance

bitmex, binance = init_exchanges()
logging.info("APIs initialized.")

# ==== REDIS QUEUE SETUP ====

redis = None

async def init_redis():
    global redis
    redis = await aioredis.from_url(CONFIG['redis_url'])
    logging.info("Connected to Redis.")

# ==== REAL-TIME DATA VIA WEBSOCKET ====

class MarketDataAggregator:
    def __init__(self):
        self.bitmex_price = None
        self.binance_price = None
        self.bitmex_funding = None
        self.binance_funding = None

    async def binance_ws(self):
        async with websockets.connect(CONFIG['websocket_uri_binance']) as ws:
            async for message in ws:
                data = json.loads(message)
                self.binance_price = float(data['c'])  # Last price
                await asyncio.sleep(0)

    async def bitmex_ws(self):
        async with websockets.connect(CONFIG['websocket_uri_bitmex']) as ws:
            async for message in ws:
                data = json.loads(message)
                # Extract price and funding rate from BitMEX update
                if 'data' in data:
                    for item in data['data']:
                        if 'lastPrice' in item:
                            self.bitmex_price = float(item['lastPrice'])
                        if 'fundingRate' in item:
                            self.bitmex_funding = float(item['fundingRate'])
                await asyncio.sleep(0)

    async def fetch_binance_funding(self):
        try:
            rates = await binance.fapiPublicGetFundingRate({'symbol': 'BTCUSDT', 'limit': 1})
            self.binance_funding = float(rates[0]['fundingRate'])
        except Exception as e:
            logging.error(f"Binance funding fetch error: {e}")

# ==== RISK MANAGEMENT ====

class RiskManager:
    def __init__(self, capital):
        self.initial_capital = capital
        self.max_dd = CONFIG['risk_limit']

    def position_size(self, price, remaining_levels):
        equity = self.initial_capital * (1 - self.max_dd)
        weight = 1.0 / (remaining_levels + 1)
        size = equity * weight / price
        return size

    def stop_condition(self, pnl):
        dd = pnl / self.initial_capital
        if dd <= -self.max_dd:
            logging.warning(f"Maximum drawdown reached ({dd:.2f}), halting trading.")
            return True
        return False

risk_manager = RiskManager(200000)

# ==== ARBITRAGE & DCA LOGIC ====

class ArbitrageDCA:
    def __init__(self, market_data):
        self.level = 0
        self.market_data = market_data
        self.executed_trades = 0

    async def execute_cycle(self):
        await self.market_data.fetch_binance_funding()
        bitmex_fr = self.market_data.bitmex_funding
        binance_fr = self.market_data.binance_funding
        bitmex_price = self.market_data.bitmex_price
        binance_price = self.market_data.binance_price

        if None in [bitmex_fr, binance_fr, bitmex_price, binance_price]:
            logging.warning("Market data incomplete, skipping cycle.")
            return

        funding_diff = bitmex_fr - binance_fr
        spread = bitmex_price - binance_price
        funding_diff_gauge.set(funding_diff)
        spread_gauge.set(spread)

        logging.info(f"Funding diff: {funding_diff:.6f}, Prices: BitMEX={bitmex_price}, Binance={binance_price}")

        if abs(funding_diff) >= CONFIG['funding_threshold']:
            # Determine which exchange to long/short
            long_exch, short_exch = ('bitmex', 'binance') if funding_diff < 0 else ('binance', 'bitmex')
            long_side, short_side = 'buy', 'sell'
            price_for_size = min(bitmex_price, binance_price)
            size = risk_manager.position_size(price_for_size, CONFIG['max_dca_levels'] - self.level)

            await self.queue_order(long_exch, long_side, size)
            await self.queue_order(short_exch, short_side, size)

            self.level += 1
            self.executed_trades += 1
            executed_trades_gauge.set(self.executed_trades)

            logging.info(f"Arbitrage trade executed: Long {long_exch} / Short {short_exch} Size: {size}")

        # DCA re-entry logic
        if self.level < CONFIG['max_dca_levels']:
            adj_price = binance_price * (1 - CONFIG['dca_step_pct']/100)
            size = risk_manager.position_size(adj_price, CONFIG['max_dca_levels'] - self.level)
            logging.info(f"DCA Level {self.level}: Size={size} at Adj Price={adj_price}")
            self.level += 1

    async def queue_order(self, exchange, side, size):
        order = {"exchange": exchange, "side": side, "size": size, "timestamp": datetime.utcnow().isoformat()}
        await redis.lpush("order_queue", json.dumps(order))
        logging.info(f"Queued order: {order}")

async def order_executor():
    while True:
        order_json = await redis.rpop("order_queue")
        if order_json:
            order = json.loads(order_json)
            exch = bitmex if order['exchange'] == 'bitmex' else binance
            try:
                exch.create_order(
                    CONFIG['symbol_bitmex'] if order['exchange']=='bitmex' else CONFIG['symbol_binance'],
                    'market',
                    order['side'],
                    order['size']
                )
                logging.info(f"Executed order on {order['exchange']}: {order}")
            except Exception as e:
                logging.error(f"Order execution error on {order['exchange']}: {e}")
        else:
            await asyncio.sleep(0.1)

# ==== MAIN LOOP & SERVER ====

async def main():
    await init_redis()
    market_data = MarketDataAggregator()
    arb_bot = ArbitrageDCA(market_data)
    start_http_server(CONFIG['prometheus_port'])  # Start Prometheus metrics HTTP server
    logging.info(f"Prometheus metrics server started on port {CONFIG['prometheus_port']}")

    # Run all coroutines concurrently
    await asyncio.gather(
        market_data.binance_ws(),
        market_data.bitmex_ws(),
        order_executor(),
        run_bot(arb_bot)
    )

async def run_bot(bot):
    while True:
        await bot.execute_cycle()
        await asyncio.sleep(1)

# Uncomment below line to run the bot
# asyncio.run(main())

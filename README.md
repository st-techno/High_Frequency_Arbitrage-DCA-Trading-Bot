Core Institutional-Grade Features
Dynamic Risk Management: Allocates dynamic position sizes per level and enforces stop-out on drawdowns.​

DCA-Driven Hedging: Executes layered BitMEX positions based on funding arbitrage or EMA crossovers.​

Arbitrage Logic: Includes funding-rate divergence detection and cross-market hedging against IBIT ETF exposure.​

Backtesting Engine: Modular compatibility with backtesting.py for parameter optimization.

Logging & Monitoring: File-based trade logs mirror compliance-grade audit trails per execution and exception.​

Async Execution Loop: Utilizes event-driven asynchronous logic for high reliability under low-latency perps markets.

## Core Institutional Features

Cross-exchange funding-rate arbitrage: Opens a long on the exchange with lower funding and short on the one with higher funding.​

DCA logic per leg: Gradually scales into legs at pre-set percentage deltas, reducing timing risk.​

Dynamic hedging: Maintains neutral delta exposure through synchronized position management on both venues.​

Resilient async engine: Async execution ensures minimal latency in live trading.

Backtest-ready architecture: Can replay historical OHLCV and funding data for model validation.

Full logging & stop-out enforcement: Captures trades and drawdown metrics for compliance auditing.

Redis Micro-Queues: Using Redis lpush and rpop as an order queue for asynchronous and fault-tolerant order execution.

Prometheus Metrics: Gauges for funding rate difference, price spread, and executed trade count, exposed on an HTTP server for real-time monitoring.

WebSocket Data Aggregation: Real-time price & funding rate streams from Binance and BitMEX via WebSocket, drastically reducing latency over REST polling.

Async Architecture: Full asynchronous design leveraging Python asyncio for concurrency and responsiveness essential in high-frequency arbitrage.

DCA & Risk Logic: Layered position sizing and entry adjustments for robustness with capital and drawdown limits.

Comprehensive Logging: Detailed logs for orders, execution errors, and state changes for audit and compliance.




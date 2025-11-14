
# Product Requirements Document (PRD): BTC-USDT Perpetual Arbitrage DCA Trading Bot

Product Requirements Document (PRD) specification designed for an institutional-grade, cross-exchange BTC-USDT Perpetual Arbitrage Trading Bot supporting BitMEX and Binance, with Redis micro-queues, 
Prometheus health checks, and WebSocket aggregation. This spec is reverse-engineered from the provided Python solution.

# Product Overview

The Arbitrage DCA Trading Bot enables automated and scalable high-frequency arbitrage between BitMEX and Binance BTC/USDT perpetual contracts. 

The bot leverages differences in perpetual funding rates, implements dynamic DCA strategies, and ensures robust risk and operational controls via Redis-powered queuing, Prometheus health metrics, and real-time WebSocket data aggregation.

## Objectives

Capture funding rate arbitrage systematically between BitMEX and Binance using BTC/USDT perpetual markets.

Manage entry risk with dollar-cost-averaging (DCA) and dynamic position sizing based on drawdown limits.

Ensure high reliability and scalability with Redis-based micro-queues for event-driven trade processing.

Enable real-time observability using Prometheus health checks and metrics.

Minimize latency by leveraging WebSocket-based live market data ingestion.

Guarantee compliance and auditability with detailed logging and error handling.

## Functional Requirements

1. Exchange Connectivity

Connect securely via API keys to BitMEX and Binance futures APIs.

Support switching between live and testnet environments.

2. Market Data Ingestion

Aggregate real-time market prices and funding rates using WebSocket feeds:

BitMEX: Price and funding stream

Binance: Price ticker and periodic funding stream

3. Arbitrage Logic

Monitor perpetual funding rate differences between exchanges.

Define arbitrage entry when funding rate differential exceeds a configurable threshold.

On signal, open offsetting long/short positions:

Long on exchange with lower funding rate, short on higher.

4. DCA Position Management

Dynamically size initial and subsequent positions based on remaining DCA levels, available capital, and drawdown settings.

Re-enter positions at preset intervals (percentage basis) to reduce timing and slippage risk.

5. Risk Management

Set max capital allocation per cycle and max drawdown.

Auto-halt trading if drawdown breaches configured limit.

6. Event-Driven Order Execution

Queue orders using Redis micro-queues (lpush, rpop).

Asynchronously handle trade submissions and monitor order status/failures.

Retry failed orders on transient errors.

7. Observability & Health Monitoring

Expose Prometheus-compatible HTTP metrics:

Funding rate differential

Price spread

Number of executed trades

Health endpoint for process liveness/readiness probes.

8. Logging & Auditing

Log trade execution, DCA cycles, arbitrage triggers, funding rates, price changes, and all errors with UTC timestamps.

Archive logs for compliance audits and incident analysis.

9. Backtesting (Optional)

Modular backtest engine for validating DCA/arbitrage strategies with historical OHLCV and funding curves.

## Non-Functional Requirements

Latency: Sub-second response from data ingestion to execution, enabled by async design.

Reliability: Redis-backed persistent queues; retries on failure; graceful error handling.

Security: API keys encrypted at rest and masked in logs.

Scalability: Multiple concurrent bots can run for different asset pairs/exchanges.

Compliance: All order and error logs timestamped and traceable.

## User Stories

As a quant trader, deploy the bot and configure capital, risk, and arbitrage parameters to fit my fund’s mandates.

As an ops engineer, monitor aggregate health and trade metrics in Prometheus and use logs for incident analysis.

As a compliance officer, trace all order events and risk controls via logs for regulatory audits.

## Acceptance Criteria

Bot opens/hedges live positions on both exchanges when funding arbitrage conditions are met.

All orders are queued and executed reliably via Redis logic.

Real-time metrics are available through Prometheus HTTP endpoints.

System halts if drawdown exceeds preset limits.

Actionable error logs and trade events are kept for at least 1 year.

Backtest results can be produced on demand (if enabled).

## Out-of-Scope (for MVP)

Arbitrage beyond BTC/USDT

GUI dashboard (can be built separately—metrics/logs provide observability)

Manual trade override (future module possible)




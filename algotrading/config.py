"""
Configuration file for algorithmic trading system
"""

# Broker Settings
INITIAL_CAPITAL = 100000
COMMISSION = 0.001  # 0.1% per trade
SLIPPAGE = 0.0005   # 0.05% slippage

# Data Settings
DATA_START_DATE = "2020-01-01"
DATA_END_DATE = "2024-12-31"
SYMBOLS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

# Strategy Parameters
STRATEGIES_CONFIG = {
    "SMA_Crossover": {
        "fast_period": 20,
        "slow_period": 50,
        "enabled": True
    },
    "RSI_Strategy": {
        "rsi_period": 14,
        "oversold": 30,
        "overbought": 70,
        "enabled": True
    },
    "MACD_Strategy": {
        "fast_ema": 12,
        "slow_ema": 26,
        "signal": 9,
        "enabled": True
    },
    "BollingerBands": {
        "period": 20,
        "dev_factor": 2,
        "enabled": True
    }
}

# Risk Management
RISK_CONFIG = {
    "max_position_size": 0.2,  # Max 20% of portfolio per position
    "stop_loss_pct": 0.05,      # 5% stop loss
    "take_profit_pct": 0.15,    # 15% take profit
    "max_positions": 5,         # Maximum concurrent positions
    "risk_per_trade": 0.02      # Risk 2% of capital per trade
}

# Performance Settings
BENCHMARK = "SPY"  # S&P 500 as benchmark
RISK_FREE_RATE = 0.02  # 2% annual risk-free rate

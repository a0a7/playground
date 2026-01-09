"""
Main entry point for algorithmic trading backtesting system
"""
import backtrader as bt
from data_handler import DataHandler
from backtest_engine import BacktestEngine
from strategies import (
    SMACrossover, RSIStrategy, MACDStrategy, 
    BollingerBandsStrategy, MultiStrategyPortfolio
)
from config import *
import warnings
warnings.filterwarnings('ignore')


def run_single_strategy():
    """Run backtest on a single strategy"""
    print("\n" + "="*60)
    print("SINGLE STRATEGY BACKTEST")
    print("="*60)
    
    # Download data
    handler = DataHandler(
        symbols=SYMBOLS[0],  # Just Apple for single strategy
        start_date=DATA_START_DATE,
        end_date=DATA_END_DATE
    )
    handler.download_data(SYMBOLS[0])
    
    # Setup backtest
    engine = BacktestEngine(
        initial_cash=INITIAL_CAPITAL,
        commission=COMMISSION
    )
    engine.setup_cerebro()
    
    # Add data
    feed = handler.get_backtrader_feed(SYMBOLS[0])
    engine.add_data(feed, name=SYMBOLS[0])
    
    # Add strategy - MultiStrategyPortfolio
    engine.add_strategy(
        MultiStrategyPortfolio,
        printlog=False,
        stop_loss=RISK_CONFIG['stop_loss_pct'],
        take_profit=RISK_CONFIG['take_profit_pct'],
        max_position_size=RISK_CONFIG['max_position_size']
    )
    
    # Run backtest
    results = engine.run(plot=False)
    
    # Print metrics
    engine.print_metrics()
    
    return engine, results


def run_strategy_comparison():
    """Compare multiple strategies on the same data"""
    print("\n" + "="*60)
    print("STRATEGY COMPARISON BACKTEST")
    print("="*60)
    
    # Download data
    handler = DataHandler(
        symbols=SYMBOLS[0],
        start_date=DATA_START_DATE,
        end_date=DATA_END_DATE
    )
    handler.download_data(SYMBOLS[0])
    feed_template = handler.get_backtrader_feed(SYMBOLS[0])
    
    strategies = [
        (SMACrossover, "SMA Crossover", {'fast': 20, 'slow': 50}),
        (RSIStrategy, "RSI Strategy", {'rsi_period': 14, 'oversold': 30, 'overbought': 70}),
        (MACDStrategy, "MACD Strategy", {'fast_ema': 12, 'slow_ema': 26, 'signal': 9}),
        (BollingerBandsStrategy, "Bollinger Bands", {'period': 20, 'devfactor': 2}),
        (MultiStrategyPortfolio, "Multi-Strategy", {'fast_sma': 20, 'slow_sma': 50})
    ]
    
    results_list = []
    strategy_names = []
    
    for strategy_class, name, params in strategies:
        print(f"\nRunning {name}...")
        
        # Create new engine for each strategy
        engine = BacktestEngine(
            initial_cash=INITIAL_CAPITAL,
            commission=COMMISSION
        )
        engine.setup_cerebro()
        
        # Add fresh data feed
        handler_temp = DataHandler(
            symbols=SYMBOLS[0],
            start_date=DATA_START_DATE,
            end_date=DATA_END_DATE
        )
        handler_temp.download_data(SYMBOLS[0])
        feed = handler_temp.get_backtrader_feed(SYMBOLS[0])
        engine.add_data(feed, name=SYMBOLS[0])
        
        # Add strategy with risk management
        engine.add_strategy(
            strategy_class,
            printlog=False,
            stop_loss=RISK_CONFIG['stop_loss_pct'],
            take_profit=RISK_CONFIG['take_profit_pct'],
            max_position_size=RISK_CONFIG['max_position_size'],
            **params
        )
        
        # Run
        result = engine.run(plot=False)
        results_list.append(result)
        strategy_names.append(name)
    
    # Compare results
    comparison_df = BacktestEngine(INITIAL_CAPITAL, COMMISSION).compare_strategies(
        results_list, 
        strategy_names
    )
    
    return comparison_df


def run_portfolio_backtest():
    """Run backtest on multiple symbols"""
    print("\n" + "="*60)
    print("MULTI-SYMBOL PORTFOLIO BACKTEST")
    print("="*60)
    
    # Download data for all symbols
    handler = DataHandler(
        symbols=SYMBOLS,
        start_date=DATA_START_DATE,
        end_date=DATA_END_DATE
    )
    handler.download_all()
    
    # Setup backtest
    engine = BacktestEngine(
        initial_cash=INITIAL_CAPITAL,
        commission=COMMISSION
    )
    engine.setup_cerebro()
    
    # Add all data feeds
    feeds = handler.get_all_feeds()
    for symbol, feed in feeds.items():
        engine.add_data(feed, name=symbol)
        print(f"Added {symbol} to portfolio")
    
    # Add strategy for first data feed (main one)
    engine.add_strategy(
        MultiStrategyPortfolio,
        printlog=False,
        stop_loss=RISK_CONFIG['stop_loss_pct'],
        take_profit=RISK_CONFIG['take_profit_pct'],
        max_position_size=RISK_CONFIG['max_position_size'] / len(SYMBOLS)  # Divide by number of symbols
    )
    
    # Run backtest
    results = engine.run(plot=False)
    
    # Print metrics
    engine.print_metrics()
    
    return engine, results


def main():
    """Main function to run backtests"""
    print("\n" + "#"*60)
    print("#" + " "*18 + "ALGO TRADING SYSTEM" + " "*21 + "#")
    print("#"*60)
    
    # Menu
    print("\nSelect backtest mode:")
    print("1. Single Strategy (AAPL)")
    print("2. Compare Multiple Strategies (AAPL)")
    print("3. Multi-Symbol Portfolio")
    print("4. Run All")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        run_single_strategy()
    elif choice == "2":
        run_strategy_comparison()
    elif choice == "3":
        run_portfolio_backtest()
    elif choice == "4":
        print("\n>>> Running Single Strategy Backtest...")
        run_single_strategy()
        
        print("\n>>> Running Strategy Comparison...")
        run_strategy_comparison()
        
        print("\n>>> Running Portfolio Backtest...")
        run_portfolio_backtest()
    else:
        print("Invalid choice. Running single strategy by default.")
        run_single_strategy()


if __name__ == "__main__":
    main()

"""
Demo script to automatically run backtests
"""
import backtrader as bt
from data_handler import DataHandler
from backtest_engine import BacktestEngine
from benchmarks import BenchmarkComparator
from strategies import (
    SMACrossover, RSIStrategy, MACDStrategy, 
    BollingerBandsStrategy, MultiStrategyPortfolio
)
from config import *
import warnings
warnings.filterwarnings('ignore')


def demo_single_strategy():
    """Demo: Run backtest on a single strategy"""
    print("\n" + "="*70)
    print("DEMO: SINGLE STRATEGY BACKTEST (Multi-Strategy Portfolio on AAPL)")
    print("="*70)
    
    # Download data
    print("\n[1/4] Downloading AAPL data...")
    handler = DataHandler(
        symbols="AAPL",
        start_date="2020-01-01",
        end_date="2024-12-31"
    )
    handler.download_data("AAPL")
    
    # Setup backtest
    print("[2/4] Setting up backtest engine...")
    engine = BacktestEngine(
        initial_cash=100000,
        commission=0.001
    )
    engine.setup_cerebro()
    
    # Add data
    print("[3/4] Adding data feed...")
    feed = handler.get_backtrader_feed("AAPL")
    engine.add_data(feed, name="AAPL")
    
    # Add strategy
    engine.add_strategy(
        MultiStrategyPortfolio,
        printlog=False,
        stop_loss=0.05,
        take_profit=0.15,
        max_position_size=0.2
    )
    
    # Run backtest
    print("[4/4] Running backtest...\n")
    results = engine.run(plot=False)
    
    # Print metrics and generate HTML report
    metrics = engine.print_metrics(
        generate_html=True,
        open_browser=True,
        strategy_name="Multi-Strategy Portfolio",
        symbol="AAPL",
        start_date="2020-01-01",
        end_date="2024-12-31"
    )
    
    return engine, results, metrics


def demo_strategy_comparison():
    """Demo: Compare multiple strategies"""
    print("\n" + "="*70)
    print("DEMO: STRATEGY COMPARISON (All Strategies on AAPL)")
    print("="*70)
    
    # Download data once
    print("\n[1/3] Downloading AAPL data...")
    
    strategies = [
        (SMACrossover, "SMA Crossover (20/50)", {'fast': 20, 'slow': 50}),
        (RSIStrategy, "RSI Mean Reversion", {'rsi_period': 14, 'oversold': 30, 'overbought': 70}),
        (MACDStrategy, "MACD Trend", {'fast_ema': 12, 'slow_ema': 26, 'signal': 9}),
        (BollingerBandsStrategy, "Bollinger Bands", {'period': 20, 'devfactor': 2}),
        (MultiStrategyPortfolio, "Multi-Strategy Combo", {'fast_sma': 20, 'slow_sma': 50})
    ]
    
    results_list = []
    strategy_names = []
    
    print(f"[2/3] Running {len(strategies)} strategies...\n")
    
    for i, (strategy_class, name, params) in enumerate(strategies, 1):
        print(f"  [{i}/{len(strategies)}] Testing {name}...")
        
        # Create new engine for each strategy
        engine = BacktestEngine(initial_cash=100000, commission=0.001)
        engine.setup_cerebro()
        
        # Download fresh data
        handler = DataHandler("AAPL", "2020-01-01", "2024-12-31")
        handler.download_data("AAPL")
        feed = handler.get_backtrader_feed("AAPL")
        engine.add_data(feed, name="AAPL")
        
        # Add strategy
        engine.add_strategy(
            strategy_class,
            printlog=False,
            stop_loss=0.05,
            take_profit=0.15,
            max_position_size=0.2,
            **params
        )
        
        # Run
        result = engine.run(plot=False)
        results_list.append(result)
        strategy_names.append(name)
    
    # Compare results
    print("\n[3/3] Generating comparison report...\n")
    
    # Download and add benchmarks
    print("Adding benchmark comparisons...")
    benchmark = BenchmarkComparator("2020-01-01", "2024-12-31", initial_capital=100000)
    benchmark.download_benchmarks()
    
    # Get initial comparison
    engine_temp = BacktestEngine(100000, 0.001)
    strategy_df = engine_temp.compare_strategies(
        results_list, 
        strategy_names,
        generate_html=False,
        open_browser=False
    )
    
    # Add benchmarks to comparison
    combined_df = benchmark.add_benchmarks_to_comparison(strategy_df)
    
    # Print combined results
    print("\n" + "="*120)
    print("STRATEGY COMPARISON (including benchmarks)")
    print("="*120)
    print(combined_df.to_string(index=False))
    print("="*120 + "\n")
    
    # Generate HTML report with benchmarks
    engine_temp.report_generator.generate_comparison_report(
        combined_df,
        title="Strategy Comparison with Benchmarks"
    )
    
    import webbrowser
    import os
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"reports/comparison_{timestamp}.html"
    abs_path = os.path.abspath(report_file)
    webbrowser.open('file://' + abs_path)
    print(f"Opening comparison report in browser...")
    
    return combined_df


def demo_quick_test():
    """Quick demo with just one strategy"""
    print("\n" + "="*70)
    print("QUICK DEMO: SMA Crossover Strategy on AAPL (2020-2024)")
    print("="*70)
    
    print("\nDownloading data...")
    handler = DataHandler("AAPL", "2020-01-01", "2024-12-31")
    handler.download_data("AAPL")
    
    print("Running backtest...")
    engine = BacktestEngine(initial_cash=100000, commission=0.001)
    engine.setup_cerebro()
    engine.add_data(handler.get_backtrader_feed("AAPL"))
    engine.add_strategy(SMACrossover, fast=20, slow=50, printlog=False)
    
    results = engine.run()
    metrics = engine.print_metrics(
        generate_html=True,
        open_browser=True,
        strategy_name="SMA Crossover",
        symbol="AAPL",
        start_date="2020-01-01",
        end_date="2024-12-31"
    )
    
    print("\nTIP: Edit config.py to customize strategies and risk parameters!")
    print("TIP: Run 'python main.py' for interactive menu with more options!")
    
    return metrics


if __name__ == "__main__":
    import sys
    
    print("\n" + "#"*70)
    print("#" + " "*15 + "ALGORITHMIC TRADING DEMO SYSTEM" + " "*23 + "#")
    print("#"*70)
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "quick":
            demo_quick_test()
        elif mode == "single":
            demo_single_strategy()
        elif mode == "compare":
            demo_strategy_comparison()
        else:
            print(f"\nUnknown mode: {mode}")
            print("Usage: python demo.py [quick|single|compare]")
    else:
        # Default: run quick demo
        demo_quick_test()
        
        # Ask if user wants to see more
        print("\n" + "="*70)
        print("Would you like to see more? (Optional)")
        print("  - Press Enter to finish")
        print("  - Type 'compare' to compare all strategies")
        response = input("\nYour choice: ").strip().lower()
        
        if response == "compare":
            demo_strategy_comparison()

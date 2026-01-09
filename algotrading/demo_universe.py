"""
Demo for universe trading (SPY, QQQ, IWM) with 200-day MA filter
"""
from data_handler import DataHandler
from backtest_engine import BacktestEngine
from benchmarks import BenchmarkComparator
from universe_strategy import UniverseRotationStrategy, SimpleMAFilterStrategy
from momentum_strategy import MomentumRotationStrategy, DualMomentumStrategy, BuyAndHoldUniverse
from strategies import SMACrossover, MultiStrategyPortfolio
import warnings
warnings.filterwarnings('ignore')


def demo_universe_trading():
    """Demo: Trade universe of ETFs with 200-day MA filter"""
    print("\n" + "="*70)
    print("UNIVERSE TRADING: SPY, QQQ, IWM with 200-day MA Filter")
    print("="*70)
    
    # Universe of ETFs
    universe = ["SPY", "QQQ", "IWM"]
    start_date = "2020-01-01"
    end_date = "2024-12-31"
    
    # Download data for all symbols
    print("\n[1/4] Downloading universe data...")
    handler = DataHandler(
        symbols=universe,
        start_date=start_date,
        end_date=end_date
    )
    handler.download_all()
    
    # Setup backtest
    print("[2/4] Setting up backtest engine...")
    engine = BacktestEngine(
        initial_cash=100000,
        commission=0.001
    )
    engine.setup_cerebro()
    
    # Add all data feeds
    print("[3/4] Adding data feeds...")
    feeds = handler.get_all_feeds()
    for symbol, feed in feeds.items():
        engine.add_data(feed, name=symbol)
        print(f"  Added {symbol}")
    
    # Add universe rotation strategy
    engine.add_strategy(
        UniverseRotationStrategy,
        ma_period=200,
        fast_sma=20,
        slow_sma=50,
        printlog=False,
        stop_loss=0.05,
        take_profit=0.15,
        max_position_size=0.30  # 30% per position
    )
    
    # Run backtest
    print("[4/4] Running backtest...\n")
    results = engine.run(plot=False)
    
    # Print metrics
    metrics = engine.print_metrics(
        generate_html=True,
        open_browser=True,
        strategy_name="Universe Rotation (200-MA Filter)",
        symbol="SPY+QQQ+IWM",
        start_date=start_date,
        end_date=end_date
    )
    
    return engine, results, metrics


def demo_universe_comparison():
    """Compare different strategies on universe"""
    print("\n" + "="*70)
    print("STRATEGY COMPARISON ON UNIVERSE (SPY, QQQ, IWM)")
    print("="*70)
    
    universe = ["SPY", "QQQ", "IWM"]
    start_date = "2020-01-01"
    end_date = "2024-12-31"
    
    strategies = [
        (MomentumRotationStrategy, "Momentum Rotation (90-day, Top 2, Monthly)", {
            'lookback': 90, 'top_n': 2, 'rebalance_days': 21, 'use_ma_filter': True
        }),
        (MomentumRotationStrategy, "Aggressive Momentum (60-day, Top 1)", {
            'lookback': 60, 'top_n': 1, 'rebalance_days': 21, 'use_ma_filter': False
        }),
        (DualMomentumStrategy, "Dual Momentum (Absolute + Relative)", {
            'lookback': 60, 'top_n': 2, 'rebalance_days': 21
        }),
        (BuyAndHoldUniverse, "Buy & Hold Universe (Equal Weight)", {}),
        (UniverseRotationStrategy, "Universe Rotation (SMA 20/50 + 200-MA)", {
            'ma_period': 200, 'fast_sma': 20, 'slow_sma': 50
        }),
        (SimpleMAFilterStrategy, "Simple 200-MA Filter", {
            'ma_period': 200
        }),
    ]
    
    results_list = []
    strategy_names = []
    
    print("\n[1/3] Downloading universe data...")
    
    for i, (strategy_class, name, params) in enumerate(strategies, 1):
        print(f"\n[2/3] Running strategy {i}/{len(strategies)}: {name}...")
        
        # Download data
        handler = DataHandler(universe, start_date, end_date)
        handler.download_all()
        
        # Setup engine
        engine = BacktestEngine(initial_cash=100000, commission=0.001)
        engine.setup_cerebro()
        
        # Add all feeds
        feeds = handler.get_all_feeds()
        for symbol, feed in feeds.items():
            engine.add_data(feed, name=symbol)
        
        # Add strategy
        engine.add_strategy(
            strategy_class,
            printlog=False,
            **params
        )
        
        # Run
        result = engine.run(plot=False)
        results_list.append(result)
        strategy_names.append(name)
    
    # Download benchmarks
    print("\n[3/3] Adding benchmark comparisons...")
    benchmark = BenchmarkComparator(start_date, end_date, initial_capital=100000)
    benchmark.download_benchmarks()
    
    # Get strategy comparison
    engine_temp = BacktestEngine(100000, 0.001)
    strategy_df = engine_temp.compare_strategies(
        results_list,
        strategy_names,
        generate_html=False,
        open_browser=False
    )
    
    # Add benchmarks
    combined_df = benchmark.add_benchmarks_to_comparison(strategy_df)
    
    # Print combined results
    print("\n" + "="*120)
    print("UNIVERSE STRATEGY COMPARISON (including benchmarks)")
    print("="*120)
    print(combined_df.to_string(index=False))
    print("="*120 + "\n")
    
    # Generate HTML report
    engine_temp.report_generator.generate_comparison_report(
        combined_df,
        title="Universe Trading Comparison (SPY+QQQ+IWM)"
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


if __name__ == "__main__":
    import sys
    
    print("\n" + "#"*70)
    print("#" + " "*15 + "UNIVERSE TRADING SYSTEM" + " "*30 + "#")
    print("#"*70)
    
    print("\nSelect mode:")
    print("1. Single Universe Strategy (Rotation with 200-MA filter)")
    print("2. Compare Universe Strategies")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\nEnter choice (1-2): ").strip()
    
    if choice == "1":
        demo_universe_trading()
    elif choice == "2":
        demo_universe_comparison()
    else:
        print("Invalid choice. Running universe comparison by default.")
        demo_universe_comparison()

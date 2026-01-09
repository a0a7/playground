"""
Example usage and code snippets
"""
from data_handler import DataHandler
from backtest_engine import BacktestEngine
from strategies import SMACrossover, RSIStrategy, MultiStrategyPortfolio
import backtrader as bt


# ============================================================================
# EXAMPLE 1: Simple Backtest on Single Stock
# ============================================================================

def example_simple_backtest():
    """Simplest possible backtest"""
    
    # Step 1: Get data
    handler = DataHandler("AAPL", "2020-01-01", "2024-12-31")
    handler.download_data("AAPL")
    
    # Step 2: Create backtest
    engine = BacktestEngine(initial_cash=100000, commission=0.001)
    engine.setup_cerebro()
    
    # Step 3: Add data and strategy
    engine.add_data(handler.get_backtrader_feed("AAPL"))
    engine.add_strategy(SMACrossover, fast=20, slow=50)
    
    # Step 4: Run and see results
    results = engine.run()
    metrics = engine.print_metrics()
    
    return metrics


# ============================================================================
# EXAMPLE 2: Custom Strategy Parameters
# ============================================================================

def example_custom_parameters():
    """Test strategy with different parameters"""
    
    handler = DataHandler("MSFT", "2022-01-01", "2024-12-31")
    handler.download_data("MSFT")
    
    engine = BacktestEngine(initial_cash=50000, commission=0.002)  # Higher commission
    engine.setup_cerebro()
    engine.add_data(handler.get_backtrader_feed("MSFT"))
    
    # Custom parameters
    engine.add_strategy(
        RSIStrategy,
        rsi_period=21,          # Longer RSI period
        oversold=25,            # More extreme oversold
        overbought=75,          # More extreme overbought
        stop_loss=0.03,         # 3% stop loss
        take_profit=0.20,       # 20% take profit
        max_position_size=0.15  # 15% max position
    )
    
    results = engine.run()
    return engine.get_metrics()


# ============================================================================
# EXAMPLE 3: Test Multiple Stocks with Same Strategy
# ============================================================================

def example_multiple_stocks():
    """Test same strategy on multiple stocks"""
    
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]
    results = {}
    
    for symbol in symbols:
        print(f"\nTesting {symbol}...")
        
        handler = DataHandler(symbol, "2020-01-01", "2024-12-31")
        handler.download_data(symbol)
        
        engine = BacktestEngine(initial_cash=100000, commission=0.001)
        engine.setup_cerebro()
        engine.add_data(handler.get_backtrader_feed(symbol), name=symbol)
        engine.add_strategy(MultiStrategyPortfolio)
        
        engine.run()
        metrics = engine.get_metrics()
        
        results[symbol] = {
            'Return %': metrics['total_return_pct'],
            'Win Rate %': metrics['win_rate_pct'],
            'Sharpe': metrics['sharpe_ratio'],
            'Max DD %': metrics['max_drawdown_pct']
        }
    
    # Print comparison
    import pandas as pd
    df = pd.DataFrame(results).T
    print("\n" + "="*70)
    print("MULTI-STOCK COMPARISON")
    print("="*70)
    print(df)
    
    return results


# ============================================================================
# EXAMPLE 4: Parameter Optimization
# ============================================================================

def example_parameter_optimization():
    """Test different parameter combinations"""
    
    handler = DataHandler("AAPL", "2020-01-01", "2024-12-31")
    handler.download_data("AAPL")
    
    # Test different SMA periods
    fast_periods = [10, 20, 30]
    slow_periods = [40, 50, 60]
    
    results = []
    
    for fast in fast_periods:
        for slow in slow_periods:
            print(f"\nTesting SMA {fast}/{slow}...")
            
            engine = BacktestEngine(initial_cash=100000, commission=0.001)
            engine.setup_cerebro()
            
            # Need fresh data for each run
            handler_temp = DataHandler("AAPL", "2020-01-01", "2024-12-31")
            handler_temp.download_data("AAPL")
            engine.add_data(handler_temp.get_backtrader_feed("AAPL"))
            
            engine.add_strategy(SMACrossover, fast=fast, slow=slow, printlog=False)
            engine.run()
            metrics = engine.get_metrics()
            
            results.append({
                'Fast': fast,
                'Slow': slow,
                'Return %': metrics['total_return_pct'],
                'Sharpe': metrics['sharpe_ratio'],
                'Max DD %': metrics['max_drawdown_pct']
            })
    
    # Show best parameters
    import pandas as pd
    df = pd.DataFrame(results)
    df = df.sort_values('Return %', ascending=False)
    
    print("\n" + "="*70)
    print("PARAMETER OPTIMIZATION RESULTS (Sorted by Return)")
    print("="*70)
    print(df.to_string(index=False))
    
    return df


# ============================================================================
# EXAMPLE 5: Creating a Custom Strategy
# ============================================================================

class ExampleCustomStrategy(bt.Strategy):
    """Example of a custom strategy"""
    
    params = dict(
        sma_period=20,
        rsi_period=14,
        volume_factor=1.5,  # Volume must be 1.5x average
        stop_loss=0.05,
        take_profit=0.15
    )
    
    def __init__(self):
        self.sma = bt.ind.SMA(period=self.params.sma_period)
        self.rsi = bt.ind.RSI(period=self.params.rsi_period)
        self.volume_sma = bt.ind.SMA(self.data.volume, period=20)
        self.order = None
        self.buy_price = None
    
    def next(self):
        if self.order:
            return
        
        # Volume confirmation
        volume_ok = self.data.volume[0] > (self.volume_sma[0] * self.params.volume_factor)
        
        if not self.position:
            # Buy: Price above SMA, RSI not overbought, high volume
            if (self.data.close[0] > self.sma[0] and 
                self.rsi[0] < 70 and 
                volume_ok):
                
                cash = self.broker.getcash()
                size = int((cash * 0.2) / self.data.close[0])  # 20% position
                self.order = self.buy(size=size)
                self.buy_price = self.data.close[0]
        
        else:
            # Exit conditions
            current_return = (self.data.close[0] / self.buy_price - 1)
            
            # Stop loss
            if current_return <= -self.params.stop_loss:
                self.order = self.close()
            # Take profit
            elif current_return >= self.params.take_profit:
                self.order = self.close()
            # Technical exit: price below SMA
            elif self.data.close[0] < self.sma[0]:
                self.order = self.close()


def example_custom_strategy():
    """Test custom strategy"""
    
    handler = DataHandler("AAPL", "2020-01-01", "2024-12-31")
    handler.download_data("AAPL")
    
    engine = BacktestEngine(initial_cash=100000, commission=0.001)
    engine.setup_cerebro()
    engine.add_data(handler.get_backtrader_feed("AAPL"))
    engine.add_strategy(ExampleCustomStrategy, sma_period=20, rsi_period=14)
    
    results = engine.run()
    metrics = engine.print_metrics()
    
    return metrics


# ============================================================================
# EXAMPLE 6: Walk-Forward Analysis (Simple Version)
# ============================================================================

def example_walk_forward():
    """Test strategy on rolling time windows"""
    
    import pandas as pd
    
    periods = [
        ("2020-01-01", "2020-12-31", "2020"),
        ("2021-01-01", "2021-12-31", "2021"),
        ("2022-01-01", "2022-12-31", "2022"),
        ("2023-01-01", "2023-12-31", "2023"),
        ("2024-01-01", "2024-12-31", "2024"),
    ]
    
    results = []
    
    for start, end, label in periods:
        print(f"\nTesting {label}...")
        
        handler = DataHandler("AAPL", start, end)
        handler.download_data("AAPL")
        
        engine = BacktestEngine(initial_cash=100000, commission=0.001)
        engine.setup_cerebro()
        engine.add_data(handler.get_backtrader_feed("AAPL"))
        engine.add_strategy(MultiStrategyPortfolio, printlog=False)
        
        engine.run()
        metrics = engine.get_metrics()
        
        results.append({
            'Period': label,
            'Return %': metrics['total_return_pct'],
            'Trades': metrics['total_trades'],
            'Win Rate %': metrics['win_rate_pct'],
            'Sharpe': metrics['sharpe_ratio']
        })
    
    df = pd.DataFrame(results)
    print("\n" + "="*70)
    print("WALK-FORWARD ANALYSIS")
    print("="*70)
    print(df.to_string(index=False))
    print(f"\nAverage Annual Return: {df['Return %'].mean():.2f}%")
    
    return df


# ============================================================================
# RUN EXAMPLES
# ============================================================================

if __name__ == "__main__":
    import sys
    
    examples = {
        "1": ("Simple Backtest", example_simple_backtest),
        "2": ("Custom Parameters", example_custom_parameters),
        "3": ("Multiple Stocks", example_multiple_stocks),
        "4": ("Parameter Optimization", example_parameter_optimization),
        "5": ("Custom Strategy", example_custom_strategy),
        "6": ("Walk-Forward Analysis", example_walk_forward),
    }
    
    print("\n" + "="*70)
    print("ALGORITHMIC TRADING EXAMPLES")
    print("="*70)
    print("\nAvailable examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("\nSelect example (1-6): ").strip()
    
    if choice in examples:
        name, func = examples[choice]
        print(f"\nRunning: {name}")
        print("="*70)
        func()
    else:
        print("Invalid choice. Running example 1 by default.")
        example_simple_backtest()

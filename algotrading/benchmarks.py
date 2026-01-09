"""
Benchmark comparison utilities
"""
import yfinance as yf
import pandas as pd
from datetime import datetime


class BenchmarkComparator:
    """Compare strategy performance against benchmarks"""
    
    # Benchmark symbols
    BENCHMARKS = {
        'VOO': 'Vanguard S&P 500 ETF',
        'IVV': 'iShares Core S&P 500 ETF',
        'SWPPX': 'Schwab S&P 500 Index Fund',
        'SPY': 'SPDR S&P 500 ETF'
    }
    
    # Average annual inflation rate (can be updated)
    INFLATION_RATE = 0.03  # 3% annual inflation
    
    def __init__(self, start_date, end_date, initial_capital=100000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.benchmark_data = {}
        
    def download_benchmarks(self):
        """Download benchmark data"""
        print("\nDownloading benchmark data...")
        
        for symbol, name in self.BENCHMARKS.items():
            try:
                print(f"  Downloading {name} ({symbol})...")
                data = yf.download(
                    symbol,
                    start=self.start_date,
                    end=self.end_date,
                    progress=False
                )
                
                if not data.empty:
                    # Flatten multi-index if present
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.get_level_values(0)
                    
                    # Calculate return
                    start_price = data['Close'].iloc[0]
                    end_price = data['Close'].iloc[-1]
                    total_return = ((end_price - start_price) / start_price) * 100
                    final_value = self.initial_capital * (1 + total_return / 100)
                    
                    self.benchmark_data[symbol] = {
                        'name': name,
                        'start_price': start_price,
                        'end_price': end_price,
                        'total_return_pct': total_return,
                        'final_value': final_value
                    }
                    print(f"    {name}: {total_return:.2f}% return")
                else:
                    print(f"    Warning: No data for {symbol}")
                    
            except Exception as e:
                print(f"    Error downloading {symbol}: {e}")
        
        return self.benchmark_data
    
    def calculate_inflation_adjusted_return(self):
        """Calculate the impact of inflation"""
        # Calculate number of years
        start = datetime.strptime(self.start_date, "%Y-%m-%d")
        end = datetime.strptime(self.end_date, "%Y-%m-%d")
        years = (end - start).days / 365.25
        
        # Calculate inflation erosion
        inflation_factor = (1 + self.INFLATION_RATE) ** years
        inflation_adjusted_value = self.initial_capital / inflation_factor
        inflation_loss = ((inflation_adjusted_value - self.initial_capital) / self.initial_capital) * 100
        
        return {
            'name': f'Cash ({self.INFLATION_RATE*100:.1f}% Inflation)',
            'years': years,
            'inflation_factor': inflation_factor,
            'final_value': self.initial_capital,  # Nominal value stays same
            'real_value': inflation_adjusted_value,  # Real purchasing power
            'total_return_pct': 0.0,  # Nominal return
            'real_return_pct': inflation_loss  # Real return (negative)
        }
    
    def get_benchmark_comparison(self):
        """Get benchmark comparison data"""
        benchmarks = []
        
        # Add inflation baseline
        inflation_data = self.calculate_inflation_adjusted_return()
        benchmarks.append({
            'Strategy': inflation_data['name'],
            'Final Value': inflation_data['final_value'],
            'Return %': inflation_data['total_return_pct'],
            'Total Trades': 0,
            'Win Rate %': 0.0,
            'Profit Factor': 0.0,
            'Max DD %': inflation_data['real_return_pct'],  # Use real return as "drawdown"
            'Sharpe Ratio': 0.0
        })
        
        # Add benchmark ETFs/funds
        for symbol, data in self.benchmark_data.items():
            benchmarks.append({
                'Strategy': data['name'],
                'Final Value': data['final_value'],
                'Return %': data['total_return_pct'],
                'Total Trades': 1,  # Buy and hold = 1 trade
                'Win Rate %': 100.0 if data['total_return_pct'] > 0 else 0.0,
                'Profit Factor': 0.0,  # Not applicable for buy-and-hold
                'Max DD %': 0.0,  # Would need full price history to calculate properly
                'Sharpe Ratio': 0.0  # Would need full price history to calculate properly
            })
        
        return benchmarks
    
    def add_benchmarks_to_comparison(self, strategy_results_df):
        """Add benchmarks to existing strategy comparison DataFrame"""
        # Get benchmark data
        benchmark_rows = self.get_benchmark_comparison()
        
        # Create benchmark DataFrame
        benchmark_df = pd.DataFrame(benchmark_rows)
        
        # Combine with strategy results
        combined_df = pd.concat([strategy_results_df, benchmark_df], ignore_index=True)
        
        # Sort by return
        combined_df = combined_df.sort_values('Return %', ascending=False)
        
        return combined_df

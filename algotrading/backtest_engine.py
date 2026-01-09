"""
Backtesting engine
"""
import backtrader as bt
from datetime import datetime
import pandas as pd
import webbrowser
import os
from analyzers import PerformanceAnalyzer
from report_generator import HTMLReportGenerator


class BacktestEngine:
    """Main backtesting engine"""
    
    def __init__(self, initial_cash=100000, commission=0.001):
        self.initial_cash = initial_cash
        self.commission = commission
        self.cerebro = None
        self.results = None
        self.report_generator = HTMLReportGenerator()
        
    def setup_cerebro(self):
        """Initialize cerebro with settings"""
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(self.initial_cash)
        self.cerebro.broker.setcommission(commission=self.commission)
        
        # Add analyzers
        self.cerebro.addanalyzer(PerformanceAnalyzer, _name='performance')
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.02)
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        
        # Add observers
        self.cerebro.addobserver(bt.observers.Broker)
        self.cerebro.addobserver(bt.observers.Trades)
        self.cerebro.addobserver(bt.observers.BuySell)
        
    def add_data(self, data, name=None):
        """Add data feed to cerebro"""
        if self.cerebro is None:
            self.setup_cerebro()
        self.cerebro.adddata(data, name=name)
        
    def add_strategy(self, strategy, **kwargs):
        """Add strategy to cerebro"""
        if self.cerebro is None:
            self.setup_cerebro()
        self.cerebro.addstrategy(strategy, **kwargs)
        
    def run(self, plot=False):
        """Run backtest"""
        if self.cerebro is None:
            raise ValueError("Cerebro not initialized. Add data and strategy first.")
            
        print(f"\nStarting Portfolio Value: ${self.cerebro.broker.getvalue():,.2f}")
        
        self.results = self.cerebro.run()
        
        final_value = self.cerebro.broker.getvalue()
        print(f"Final Portfolio Value: ${final_value:,.2f}")
        print(f"Profit/Loss: ${final_value - self.initial_cash:,.2f}")
        print(f"Return: {((final_value - self.initial_cash) / self.initial_cash) * 100:.2f}%")
        
        if plot:
            self.cerebro.plot(style='candlestick', barup='green', bardown='red')
            
        return self.results
        
    def get_metrics(self):
        """Extract performance metrics"""
        if self.results is None:
            raise ValueError("No backtest results. Run backtest first.")
            
        strat = self.results[0]
        
        # Custom performance analyzer
        perf = strat.analyzers.performance.get_analysis()
        
        # Sharpe Ratio
        sharpe = strat.analyzers.sharpe.get_analysis()
        
        # Drawdown
        drawdown = strat.analyzers.drawdown.get_analysis()
        
        # Trade Analysis
        trades = strat.analyzers.trades.get_analysis()
        
        # Returns
        returns = strat.analyzers.returns.get_analysis()
        
        metrics = {
            **perf,
            'sharpe_ratio_bt': sharpe.get('sharperatio', 0),
            'max_drawdown_bt': drawdown.get('max', {}).get('drawdown', 0),
            'total_trades_bt': trades.get('total', {}).get('total', 0),
            'avg_return': returns.get('ravg', 0),
            'total_return_bt': returns.get('rtot', 0)
        }
        
        return metrics
        
    def print_metrics(self, generate_html=True, open_browser=True, 
                     strategy_name="Strategy", symbol="AAPL", 
                     start_date=None, end_date=None):
        """Print formatted metrics and optionally generate HTML report"""
        metrics = self.get_metrics()
        
        # Console output (simplified)
        print("\n" + "="*60)
        print("BACKTEST PERFORMANCE METRICS")
        print("="*60)
        
        print(f"\n{'Portfolio Performance':-^60}")
        print(f"Initial Value:          ${metrics['start_value']:>15,.2f}")
        print(f"Final Value:            ${metrics['end_value']:>15,.2f}")
        print(f"Total Return:           {metrics['total_return_pct']:>15.2f}%")
        
        print(f"\n{'Trade Statistics':-^60}")
        print(f"Total Trades:           {metrics['total_trades']:>15}")
        print(f"Winning Trades:         {metrics['winning_trades']:>15}")
        print(f"Losing Trades:          {metrics['losing_trades']:>15}")
        print(f"Win Rate:               {metrics['win_rate_pct']:>15.2f}%")
        print(f"Average Win:            ${metrics['avg_win']:>15.2f}")
        print(f"Average Loss:           ${metrics['avg_loss']:>15.2f}")
        print(f"Profit Factor:          {metrics['profit_factor']:>15.2f}")
        
        print(f"\n{'Risk Metrics':-^60}")
        print(f"Max Drawdown:           {metrics['max_drawdown_pct']:>15.2f}%")
        print(f"Sharpe Ratio:           {metrics['sharpe_ratio']:>15.2f}")
        
        print("="*60 + "\n")
        
        # Generate HTML report
        if generate_html:
            report_file = self.report_generator.generate_report(
                metrics, 
                strategy_name=strategy_name,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if open_browser:
                # Open in browser
                abs_path = os.path.abspath(report_file)
                webbrowser.open('file://' + abs_path)
                print(f"Opening report in browser...")
        
        return metrics
        
    def compare_strategies(self, results_list, strategy_names, 
                          generate_html=True, open_browser=True):
        """Compare multiple strategy results"""
        comparison = []
        
        for result, name in zip(results_list, strategy_names):
            strat = result[0]
            perf = strat.analyzers.performance.get_analysis()
            
            comparison.append({
                'Strategy': name,
                'Final Value': perf['end_value'],
                'Return %': perf['total_return_pct'],
                'Total Trades': perf['total_trades'],
                'Win Rate %': perf['win_rate_pct'],
                'Profit Factor': perf['profit_factor'],
                'Max DD %': perf['max_drawdown_pct'],
                'Sharpe Ratio': perf['sharpe_ratio']
            })
            
        df = pd.DataFrame(comparison)
        df = df.sort_values('Return %', ascending=False)
        
        print("\n" + "="*100)
        print("STRATEGY COMPARISON")
        print("="*100)
        print(df.to_string(index=False))
        print("="*100 + "\n")
        
        # Generate HTML report
        if generate_html:
            report_file = self.report_generator.generate_comparison_report(
                df, 
                title="Strategy Comparison"
            )
            
            if open_browser:
                abs_path = os.path.abspath(report_file)
                webbrowser.open('file://' + abs_path)
                print(f"Opening comparison report in browser...")
        
        return df

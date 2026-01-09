"""
HTML Report Generator for Backtest Results
"""
import os
from datetime import datetime
import json


class HTMLReportGenerator:
    """Generate beautiful HTML reports for backtest results"""
    
    def __init__(self, output_dir="reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_report(self, metrics, strategy_name="Strategy", symbol="AAPL", 
                       start_date=None, end_date=None, trades_data=None):
        """Generate a comprehensive HTML report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/{strategy_name.replace(' ', '_')}_{symbol}_{timestamp}.html"
        
        html = self._create_html(metrics, strategy_name, symbol, start_date, end_date, trades_data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\nReport generated: {filename}")
        return filename
    
    def generate_comparison_report(self, comparison_df, title="Strategy Comparison"):
        """Generate comparison report for multiple strategies"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.output_dir}/comparison_{timestamp}.html"
        
        html = self._create_comparison_html(comparison_df, title)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\nComparison report generated: {filename}")
        return filename
    
    def _create_html(self, metrics, strategy_name, symbol, start_date, end_date, trades_data):
        """Create HTML content for single strategy report"""
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backtest Report - {strategy_name}</title>
    <style>
        body {{
            font-family: 'Courier New', Courier, monospace;
            background: white;
            color: black;
            padding: 40px;
            max-width: 900px;
            margin: 0 auto;
            line-height: 1.6;
        }}
        
        h1 {{
            border-bottom: 2px solid black;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        h2 {{
            border-bottom: 1px solid black;
            padding-bottom: 5px;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        th {{
            text-align: left;
            border-bottom: 2px solid black;
            padding: 10px 5px;
        }}
        
        td {{
            padding: 8px 5px;
            border-bottom: 1px solid #ccc;
        }}
        
        tr:last-child td {{
            border-bottom: 2px solid black;
        }}
        
        .right {{
            text-align: right;
        }}
        
        .header-info {{
            margin-bottom: 30px;
        }}
        
        .header-info div {{
            margin: 5px 0;
        }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid black;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>BACKTEST REPORT</h1>
    
    <div class="header-info">
        <div>Strategy: {strategy_name}</div>
        <div>Symbol: {symbol}</div>
        <div>Period: {start_date or 'N/A'} to {end_date or 'N/A'}</div>
        <div>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>
    
    <h2>PORTFOLIO PERFORMANCE</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th class="right">Value</th>
        </tr>
        <tr>
            <td>Initial Capital</td>
            <td class="right">${metrics['start_value']:,.2f}</td>
        </tr>
        <tr>
            <td>Final Value</td>
            <td class="right">${metrics['end_value']:,.2f}</td>
        </tr>
        <tr>
            <td>Profit/Loss</td>
            <td class="right">${metrics['end_value'] - metrics['start_value']:+,.2f}</td>
        </tr>
        <tr>
            <td>Return</td>
            <td class="right">{metrics['total_return_pct']:+.2f}%</td>
        </tr>
    </table>
    
    <h2>TRADE STATISTICS</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th class="right">Value</th>
        </tr>
        <tr>
            <td>Total Trades</td>
            <td class="right">{metrics['total_trades']}</td>
        </tr>
        <tr>
            <td>Winning Trades</td>
            <td class="right">{metrics['winning_trades']}</td>
        </tr>
        <tr>
            <td>Losing Trades</td>
            <td class="right">{metrics['losing_trades']}</td>
        </tr>
        <tr>
            <td>Win Rate</td>
            <td class="right">{metrics['win_rate_pct']:.2f}%</td>
        </tr>
        <tr>
            <td>Average Win</td>
            <td class="right">${metrics['avg_win']:,.2f}</td>
        </tr>
        <tr>
            <td>Average Loss</td>
            <td class="right">${metrics['avg_loss']:,.2f}</td>
        </tr>
        <tr>
            <td>Profit Factor</td>
            <td class="right">{metrics['profit_factor']:.2f}</td>
        </tr>
    </table>
    
    <h2>RISK METRICS</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th class="right">Value</th>
        </tr>
        <tr>
            <td>Maximum Drawdown</td>
            <td class="right">{metrics['max_drawdown_pct']:.2f}%</td>
        </tr>
        <tr>
            <td>Sharpe Ratio</td>
            <td class="right">{metrics['sharpe_ratio']:.2f}</td>
        </tr>
    </table>
    
    <div class="footer">
        Generated by Algorithmic Trading System - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
</body>
</html>
"""
        return html
    
    def _create_comparison_html(self, comparison_df, title):
        """Create HTML for strategy comparison"""
        
        # Convert DataFrame to dict for easier access
        strategies = comparison_df.to_dict('records')
        
        # Separate strategies from benchmarks
        algo_strategies = [s for s in strategies if s['Total Trades'] > 1]
        benchmarks = [s for s in strategies if s['Total Trades'] <= 1]
        
        best_strategy = algo_strategies[0] if algo_strategies else strategies[0]
        
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: 'Courier New', Courier, monospace;
            background: white;
            color: black;
            padding: 40px;
            max-width: 1200px;
            margin: 0 auto;
            line-height: 1.6;
        }}
        
        h1 {{
            border-bottom: 2px solid black;
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        
        h2 {{
            border-bottom: 1px solid black;
            padding-bottom: 5px;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        th {{
            text-align: left;
            border-bottom: 2px solid black;
            padding: 10px 5px;
        }}
        
        td {{
            padding: 8px 5px;
            border-bottom: 1px solid #ccc;
        }}
        
        tr:last-child td {{
            border-bottom: 2px solid black;
        }}
        
        .right {{
            text-align: right;
        }}
        
        .best {{
            background: #f0f0f0;
        }}
        
        .benchmark {{
            background: #f9f9f9;
        }}
        
        .winner-box {{
            border: 2px solid black;
            padding: 20px;
            margin: 20px 0 30px 0;
        }}
        
        .winner-box div {{
            margin: 5px 0;
        }}
        
        .info-box {{
            border: 1px solid black;
            padding: 15px;
            margin: 20px 0;
            background: #fafafa;
        }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid black;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <h1>{title.upper()}</h1>
    
    <div class="winner-box">
        <div><strong>TOP PERFORMING STRATEGY: {best_strategy['Strategy']}</strong></div>
        <div>Final Value: ${best_strategy['Final Value']:,.2f}</div>
        <div>Return: {best_strategy['Return %']:.2f}%</div>
        <div>Win Rate: {best_strategy['Win Rate %']:.1f}%</div>
        <div>Sharpe Ratio: {best_strategy['Sharpe Ratio']:.2f}</div>
    </div>
    
    <h2>ALGORITHMIC TRADING STRATEGIES</h2>
    <table>
        <tr>
            <th>Rank</th>
            <th>Strategy</th>
            <th class="right">Final Value</th>
            <th class="right">Return %</th>
            <th class="right">Trades</th>
            <th class="right">Win Rate %</th>
            <th class="right">Profit Factor</th>
            <th class="right">Max DD %</th>
            <th class="right">Sharpe</th>
        </tr>
"""
        
        # Add algo strategy rows
        for i, strat in enumerate(algo_strategies, 1):
            row_class = 'best' if i == 1 else ''
            
            html += f"""
        <tr class="{row_class}">
            <td>{i}</td>
            <td>{strat['Strategy']}</td>
            <td class="right">${strat['Final Value']:,.2f}</td>
            <td class="right">{strat['Return %']:+.2f}%</td>
            <td class="right">{strat['Total Trades']:.0f}</td>
            <td class="right">{strat['Win Rate %']:.1f}%</td>
            <td class="right">{strat['Profit Factor']:.2f}</td>
            <td class="right">{strat['Max DD %']:.2f}%</td>
            <td class="right">{strat['Sharpe Ratio']:.2f}</td>
        </tr>
"""
        
        html += """
    </table>
    
    <h2>BENCHMARK COMPARISON</h2>
    <div class="info-box">
        Benchmarks represent passive buy-and-hold investments in S&P 500 index funds
        with the same initial capital and time period. This provides context for 
        evaluating algorithmic trading performance.
    </div>
    <table>
        <tr>
            <th>Benchmark</th>
            <th class="right">Final Value</th>
            <th class="right">Return %</th>
            <th class="right">Type</th>
        </tr>
"""
        
        # Add benchmark rows
        for bench in benchmarks:
            bench_type = "Inflation Baseline" if "Inflation" in bench['Strategy'] else "S&P 500 Index"
            
            html += f"""
        <tr class="benchmark">
            <td>{bench['Strategy']}</td>
            <td class="right">${bench['Final Value']:,.2f}</td>
            <td class="right">{bench['Return %']:+.2f}%</td>
            <td class="right">{bench_type}</td>
        </tr>
"""
        
        html += f"""
    </table>
    
    <h2>COMPLETE RANKING</h2>
    <table>
        <tr>
            <th>Rank</th>
            <th>Strategy/Benchmark</th>
            <th class="right">Final Value</th>
            <th class="right">Return %</th>
        </tr>
"""
        
        # Add all strategies ranked together
        for i, strat in enumerate(strategies, 1):
            is_benchmark = strat['Total Trades'] <= 1
            row_class = 'benchmark' if is_benchmark else ('best' if i == 1 else '')
            
            html += f"""
        <tr class="{row_class}">
            <td>{i}</td>
            <td>{strat['Strategy']}</td>
            <td class="right">${strat['Final Value']:,.2f}</td>
            <td class="right">{strat['Return %']:+.2f}%</td>
        </tr>
"""
        
        html += f"""
    </table>
    
    <div class="footer">
        Generated by Algorithmic Trading System - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        <br>
        Note: Benchmark Max DD and Sharpe Ratio require full historical data analysis and are not calculated here.
    </div>
</body>
</html>
"""
        return html

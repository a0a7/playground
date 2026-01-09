"""
Custom analyzers for performance metrics
"""
import backtrader as bt
import numpy as np
from datetime import datetime


class PerformanceAnalyzer(bt.Analyzer):
    """Comprehensive performance analyzer"""
    
    def __init__(self):
        self.start_value = self.strategy.broker.getvalue()
        self.end_value = None
        self.pnl = []
        self.trades = []
        self.drawdown = []
        self.peak = self.start_value
        
    def notify_trade(self, trade):
        if trade.isclosed:
            self.trades.append({
                'pnl': trade.pnl,
                'pnlcomm': trade.pnlcomm,
                'size': trade.size,
                'price': trade.price,
                'value': trade.value,
                'commission': trade.commission
            })
            
    def next(self):
        value = self.strategy.broker.getvalue()
        self.pnl.append(value - self.start_value)
        
        # Track drawdown
        if value > self.peak:
            self.peak = value
        drawdown = (self.peak - value) / self.peak
        self.drawdown.append(drawdown)
        
    def stop(self):
        self.end_value = self.strategy.broker.getvalue()
        
    def get_analysis(self):
        total_return = (self.end_value - self.start_value) / self.start_value
        
        # Trade statistics
        winning_trades = [t for t in self.trades if t['pnlcomm'] > 0]
        losing_trades = [t for t in self.trades if t['pnlcomm'] <= 0]
        
        total_trades = len(self.trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        avg_win = np.mean([t['pnlcomm'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnlcomm'] for t in losing_trades]) if losing_trades else 0
        
        profit_factor = (sum([t['pnlcomm'] for t in winning_trades]) / 
                        abs(sum([t['pnlcomm'] for t in losing_trades])) 
                        if losing_trades and sum([t['pnlcomm'] for t in losing_trades]) != 0 else 0)
        
        max_drawdown = max(self.drawdown) if self.drawdown else 0
        
        # Sharpe Ratio (simplified - assuming daily data)
        if len(self.pnl) > 1:
            returns = np.diff(self.pnl) / self.start_value
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe = 0
            
        return {
            'start_value': self.start_value,
            'end_value': self.end_value,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'win_rate_pct': win_rate * 100,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown * 100,
            'sharpe_ratio': sharpe
        }

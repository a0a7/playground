"""
Trading strategies for backtesting
"""
import backtrader as bt
import numpy as np


class BaseStrategy(bt.Strategy):
    """Base strategy with risk management"""
    
    params = dict(
        stop_loss=0.05,
        take_profit=0.15,
        max_position_size=0.2,
        printlog=True
    )
    
    def __init__(self):
        self.order = None
        self.buy_price = None
        self.buy_comm = None
        
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.buy_comm = order.executed.comm
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, '
                        f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            else:
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, '
                        f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
            
        self.order = None
        
    def notify_trade(self, trade):
        if not trade.isclosed:
            return
            
        self.log(f'TRADE PROFIT, GROSS: {trade.pnl:.2f}, NET: {trade.pnlcomm:.2f}')
        
    def log(self, txt, dt=None):
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
            
    def get_position_size(self):
        """Calculate position size based on portfolio value"""
        cash = self.broker.getcash()
        value = self.broker.getvalue()
        max_invest = value * self.params.max_position_size
        price = self.data.close[0]
        size = int(max_invest / price)
        return size


class SMACrossover(BaseStrategy):
    """Simple Moving Average Crossover Strategy"""
    
    params = dict(
        fast=20,
        slow=50,
        stop_loss=0.05,
        take_profit=0.15,
        max_position_size=0.2,
        printlog=False
    )
    
    def __init__(self):
        super().__init__()
        self.sma_fast = bt.ind.SMA(period=self.params.fast)
        self.sma_slow = bt.ind.SMA(period=self.params.slow)
        self.crossover = bt.ind.CrossOver(self.sma_fast, self.sma_slow)
        
    def next(self):
        if self.order:
            return
            
        if not self.position:
            # Buy signal
            if self.crossover > 0:
                size = self.get_position_size()
                self.order = self.buy(size=size)
        else:
            # Sell signals
            if self.crossover < 0:
                self.order = self.close()
            # Stop loss
            elif self.buy_price and (self.data.close[0] / self.buy_price - 1) <= -self.params.stop_loss:
                self.log('STOP LOSS TRIGGERED')
                self.order = self.close()
            # Take profit
            elif self.buy_price and (self.data.close[0] / self.buy_price - 1) >= self.params.take_profit:
                self.log('TAKE PROFIT TRIGGERED')
                self.order = self.close()


class RSIStrategy(BaseStrategy):
    """RSI Mean Reversion Strategy"""
    
    params = dict(
        rsi_period=14,
        oversold=30,
        overbought=70,
        stop_loss=0.05,
        take_profit=0.15,
        max_position_size=0.2,
        printlog=False
    )
    
    def __init__(self):
        super().__init__()
        self.rsi = bt.ind.RSI(period=self.params.rsi_period)
        
    def next(self):
        if self.order:
            return
            
        if not self.position:
            # Buy when oversold
            if self.rsi < self.params.oversold:
                size = self.get_position_size()
                self.order = self.buy(size=size)
        else:
            # Sell when overbought or stop/take profit
            if self.rsi > self.params.overbought:
                self.order = self.close()
            elif self.buy_price and (self.data.close[0] / self.buy_price - 1) <= -self.params.stop_loss:
                self.log('STOP LOSS TRIGGERED')
                self.order = self.close()
            elif self.buy_price and (self.data.close[0] / self.buy_price - 1) >= self.params.take_profit:
                self.log('TAKE PROFIT TRIGGERED')
                self.order = self.close()


class MACDStrategy(BaseStrategy):
    """MACD Strategy"""
    
    params = dict(
        fast_ema=12,
        slow_ema=26,
        signal=9,
        stop_loss=0.05,
        take_profit=0.15,
        max_position_size=0.2,
        printlog=False
    )
    
    def __init__(self):
        super().__init__()
        self.macd = bt.ind.MACD(
            period_me1=self.params.fast_ema,
            period_me2=self.params.slow_ema,
            period_signal=self.params.signal
        )
        self.crossover = bt.ind.CrossOver(self.macd.macd, self.macd.signal)
        
    def next(self):
        if self.order:
            return
            
        if not self.position:
            # Buy signal: MACD crosses above signal
            if self.crossover > 0:
                size = self.get_position_size()
                self.order = self.buy(size=size)
        else:
            # Sell signal: MACD crosses below signal
            if self.crossover < 0:
                self.order = self.close()
            elif self.buy_price and (self.data.close[0] / self.buy_price - 1) <= -self.params.stop_loss:
                self.log('STOP LOSS TRIGGERED')
                self.order = self.close()
            elif self.buy_price and (self.data.close[0] / self.buy_price - 1) >= self.params.take_profit:
                self.log('TAKE PROFIT TRIGGERED')
                self.order = self.close()


class BollingerBandsStrategy(BaseStrategy):
    """Bollinger Bands Mean Reversion Strategy"""
    
    params = dict(
        period=20,
        devfactor=2,
        stop_loss=0.05,
        take_profit=0.15,
        max_position_size=0.2,
        printlog=False
    )
    
    def __init__(self):
        super().__init__()
        self.bbands = bt.ind.BollingerBands(
            period=self.params.period,
            devfactor=self.params.devfactor
        )
        
    def next(self):
        if self.order:
            return
            
        if not self.position:
            # Buy when price touches lower band
            if self.data.close[0] < self.bbands.lines.bot[0]:
                size = self.get_position_size()
                self.order = self.buy(size=size)
        else:
            # Sell when price touches upper band or middle
            if self.data.close[0] > self.bbands.lines.top[0]:
                self.order = self.close()
            elif self.buy_price and (self.data.close[0] / self.buy_price - 1) <= -self.params.stop_loss:
                self.log('STOP LOSS TRIGGERED')
                self.order = self.close()
            elif self.buy_price and (self.data.close[0] / self.buy_price - 1) >= self.params.take_profit:
                self.log('TAKE PROFIT TRIGGERED')
                self.order = self.close()


class MultiStrategyPortfolio(BaseStrategy):
    """Portfolio strategy combining multiple signals"""
    
    params = dict(
        fast_sma=20,
        slow_sma=50,
        rsi_period=14,
        rsi_oversold=30,
        rsi_overbought=70,
        stop_loss=0.05,
        take_profit=0.15,
        max_position_size=0.15,
        printlog=False
    )
    
    def __init__(self):
        super().__init__()
        # Indicators
        self.sma_fast = bt.ind.SMA(period=self.params.fast_sma)
        self.sma_slow = bt.ind.SMA(period=self.params.slow_sma)
        self.rsi = bt.ind.RSI(period=self.params.rsi_period)
        self.macd = bt.ind.MACD()
        
    def next(self):
        if self.order:
            return
            
        # Count bullish signals
        bullish_signals = 0
        bearish_signals = 0
        
        # SMA signal
        if self.sma_fast[0] > self.sma_slow[0]:
            bullish_signals += 1
        else:
            bearish_signals += 1
            
        # RSI signal
        if self.rsi[0] < self.params.rsi_oversold:
            bullish_signals += 1
        elif self.rsi[0] > self.params.rsi_overbought:
            bearish_signals += 1
            
        # MACD signal
        if self.macd.macd[0] > self.macd.signal[0]:
            bullish_signals += 1
        else:
            bearish_signals += 1
            
        if not self.position:
            # Buy if at least 2 bullish signals
            if bullish_signals >= 2:
                size = self.get_position_size()
                self.order = self.buy(size=size)
        else:
            # Sell if at least 2 bearish signals
            if bearish_signals >= 2:
                self.order = self.close()
            elif self.buy_price and (self.data.close[0] / self.buy_price - 1) <= -self.params.stop_loss:
                self.log('STOP LOSS TRIGGERED')
                self.order = self.close()
            elif self.buy_price and (self.data.close[0] / self.buy_price - 1) >= self.params.take_profit:
                self.log('TAKE PROFIT TRIGGERED')
                self.order = self.close()

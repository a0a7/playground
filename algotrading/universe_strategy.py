"""
Multi-asset universe strategy with 200-day MA filter
"""
import backtrader as bt
from strategies import BaseStrategy


class UniverseRotationStrategy(BaseStrategy):
    """Trade multiple assets with 200-day MA filter"""
    
    params = dict(
        ma_period=200,
        fast_sma=20,
        slow_sma=50,
        stop_loss=0.05,
        take_profit=0.15,
        max_position_size=0.30,  # 30% per position (3 assets max)
        printlog=False
    )
    
    def __init__(self):
        super().__init__()
        
        # Store indicators for each data feed
        self.ma_200 = {}
        self.sma_fast = {}
        self.sma_slow = {}
        self.crossover = {}
        self.orders = {}
        self.buy_prices = {}
        
        for i, d in enumerate(self.datas):
            # 200-day MA filter
            self.ma_200[d] = bt.ind.SMA(d.close, period=self.params.ma_period)
            
            # Fast and slow SMA for signals
            self.sma_fast[d] = bt.ind.SMA(d.close, period=self.params.fast_sma)
            self.sma_slow[d] = bt.ind.SMA(d.close, period=self.params.slow_sma)
            self.crossover[d] = bt.ind.CrossOver(self.sma_fast[d], self.sma_slow[d])
            
            self.orders[d] = None
            self.buy_prices[d] = None
    
    def prenext(self):
        """Called when not all indicators are ready"""
        self.next()
    
    def next(self):
        """Trading logic"""
        for i, d in enumerate(self.datas):
            # Skip if we have pending order
            if self.orders[d]:
                continue
            
            pos = self.getposition(d)
            
            # RULE: Only trade if price > 200-day MA
            above_ma_200 = d.close[0] > self.ma_200[d][0]
            
            if not pos:
                # BUY signal: Crossover AND price above 200-day MA
                if self.crossover[d] > 0 and above_ma_200:
                    size = self.get_position_size_for_data(d)
                    if size > 0:
                        self.orders[d] = self.buy(data=d, size=size)
                        self.buy_prices[d] = d.close[0]
                        self.log(f'BUY {d._name} @ {d.close[0]:.2f}')
            else:
                # SELL signals
                sell = False
                reason = ""
                
                # Sell if crossover down
                if self.crossover[d] < 0:
                    sell = True
                    reason = "CROSSOVER DOWN"
                
                # Sell if price drops below 200-day MA
                elif not above_ma_200:
                    sell = True
                    reason = "BELOW 200-MA"
                
                # Stop loss
                elif self.buy_prices[d] and (d.close[0] / self.buy_prices[d] - 1) <= -self.params.stop_loss:
                    sell = True
                    reason = "STOP LOSS"
                
                # Take profit
                elif self.buy_prices[d] and (d.close[0] / self.buy_prices[d] - 1) >= self.params.take_profit:
                    sell = True
                    reason = "TAKE PROFIT"
                
                if sell:
                    self.orders[d] = self.close(data=d)
                    self.log(f'SELL {d._name} @ {d.close[0]:.2f} - {reason}')
                    self.buy_prices[d] = None
    
    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        # Find which data this order belongs to
        for d in self.datas:
            if self.orders[d] == order:
                if order.status in [order.Completed]:
                    if order.isbuy():
                        self.log(f'{d._name} BUY EXECUTED @ {order.executed.price:.2f}')
                    else:
                        self.log(f'{d._name} SELL EXECUTED @ {order.executed.price:.2f}')
                elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                    self.log(f'{d._name} ORDER FAILED')
                
                self.orders[d] = None
                break
    
    def get_position_size_for_data(self, data):
        """Calculate position size for specific data feed"""
        value = self.broker.getvalue()
        max_invest = value * self.params.max_position_size
        price = data.close[0]
        size = int(max_invest / price)
        return size


class SimpleMAFilterStrategy(BaseStrategy):
    """Simple strategy: Buy when above 200-MA, sell when below"""
    
    params = dict(
        ma_period=200,
        stop_loss=0.10,
        take_profit=0.20,
        max_position_size=0.30,
        printlog=False
    )
    
    def __init__(self):
        super().__init__()
        
        self.ma_200 = {}
        self.orders = {}
        self.buy_prices = {}
        
        for d in self.datas:
            self.ma_200[d] = bt.ind.SMA(d.close, period=self.params.ma_period)
            self.orders[d] = None
            self.buy_prices[d] = None
    
    def prenext(self):
        self.next()
    
    def next(self):
        for d in self.datas:
            if self.orders[d]:
                continue
            
            pos = self.getposition(d)
            above_ma = d.close[0] > self.ma_200[d][0]
            
            if not pos:
                # Buy when price crosses above 200-MA
                if above_ma and d.close[-1] <= self.ma_200[d][-1]:
                    size = self.get_position_size_for_data(d)
                    if size > 0:
                        self.orders[d] = self.buy(data=d, size=size)
                        self.buy_prices[d] = d.close[0]
                        self.log(f'BUY {d._name} @ {d.close[0]:.2f}')
            else:
                # Sell when price crosses below 200-MA
                sell = False
                reason = ""
                
                if not above_ma:
                    sell = True
                    reason = "BELOW 200-MA"
                elif self.buy_prices[d] and (d.close[0] / self.buy_prices[d] - 1) <= -self.params.stop_loss:
                    sell = True
                    reason = "STOP LOSS"
                elif self.buy_prices[d] and (d.close[0] / self.buy_prices[d] - 1) >= self.params.take_profit:
                    sell = True
                    reason = "TAKE PROFIT"
                
                if sell:
                    self.orders[d] = self.close(data=d)
                    self.log(f'SELL {d._name} @ {d.close[0]:.2f} - {reason}')
                    self.buy_prices[d] = None
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        for d in self.datas:
            if self.orders[d] == order:
                if order.status in [order.Completed]:
                    if order.isbuy():
                        self.log(f'{d._name} BUY EXECUTED @ {order.executed.price:.2f}')
                    else:
                        self.log(f'{d._name} SELL EXECUTED @ {order.executed.price:.2f}')
                elif order.status in [order.Canceled, order.Margin, order.Rejected]:
                    self.log(f'{d._name} ORDER FAILED')
                
                self.orders[d] = None
                break
    
    def get_position_size_for_data(self, data):
        value = self.broker.getvalue()
        max_invest = value * self.params.max_position_size
        price = data.close[0]
        size = int(max_invest / price)
        return size

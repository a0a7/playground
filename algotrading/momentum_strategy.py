"""
Momentum rotation strategy - Hold the strongest performers, rotate monthly
"""
import backtrader as bt
from strategies import BaseStrategy


class MomentumRotationStrategy(bt.Strategy):
    """
    Monthly momentum rotation strategy:
    1. Rank universe by momentum (returns over lookback period)
    2. Hold top N performers
    3. Rebalance monthly
    4. Use 200-day MA as market regime filter
    """
    
    params = dict(
        lookback=90,           # Momentum lookback period (90 days ~= 3 months)
        top_n=2,               # Hold top N performers (2 out of 3)
        rebalance_days=21,     # Rebalance every ~1 month (21 trading days)
        use_ma_filter=True,    # Only hold assets above 200-day MA
        ma_period=200,
        printlog=False
    )
    
    def __init__(self):
        self.day_counter = 0
        self.rebalance_day = 0
        
        # Store indicators for each asset
        self.momentum = {}
        self.ma_200 = {}
        
        for d in self.datas:
            # Simple momentum = % change over lookback period
            self.momentum[d] = bt.ind.ROC(d.close, period=self.params.lookback)
            
            # 200-day MA filter
            if self.params.use_ma_filter:
                self.ma_200[d] = bt.ind.SMA(d.close, period=self.params.ma_period)
    
    def prenext(self):
        """Called when not all indicators are ready"""
        self.next()
    
    def next(self):
        """Main trading logic"""
        self.day_counter += 1
        
        # Only rebalance on schedule
        if self.day_counter < self.rebalance_day:
            return
        
        self.rebalance_day = self.day_counter + self.params.rebalance_days
        
        # Calculate momentum scores for all assets
        rankings = []
        for d in self.datas:
            # Skip if not enough data
            if len(d) < self.params.lookback + 10:
                continue
            
            # Apply 200-day MA filter
            if self.params.use_ma_filter:
                if len(d) < self.params.ma_period:
                    continue
                if d.close[0] < self.ma_200[d][0]:
                    # Asset below 200-MA, give it negative score
                    continue
            
            # Get momentum score
            mom_score = self.momentum[d][0]
            rankings.append((d, mom_score, d._name))
        
        # Sort by momentum (highest first)
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        # Determine which assets to hold
        top_assets = set([d for d, score, name in rankings[:self.params.top_n]])
        
        # Log rotation
        if self.params.printlog:
            self.log("=" * 60)
            self.log(f"REBALANCE #{self.day_counter // self.params.rebalance_days}")
            for rank, (d, score, name) in enumerate(rankings, 1):
                status = "HOLD" if d in top_assets else "SKIP"
                self.log(f"  {rank}. {name}: {score:.2f}% momentum - {status}")
        
        # Close positions NOT in top N
        for d in self.datas:
            pos = self.getposition(d)
            if pos and d not in top_assets:
                self.close(data=d)
                if self.params.printlog:
                    self.log(f"SELL {d._name} @ {d.close[0]:.2f}")
        
        # Open/maintain positions in top N
        if len(top_assets) > 0:
            target_pct = 1.0 / len(top_assets)  # Equal weight
            
            for d in top_assets:
                pos = self.getposition(d)
                current_value = pos.size * d.close[0] if pos else 0
                target_value = self.broker.getvalue() * target_pct
                
                # Only rebalance if significantly off target (>10% difference)
                if abs(current_value - target_value) / target_value > 0.10:
                    target_size = int(target_value / d.close[0])
                    
                    if target_size > 0:
                        if pos:
                            # Adjust position
                            delta = target_size - pos.size
                            if delta > 0:
                                self.buy(data=d, size=delta)
                            elif delta < 0:
                                self.sell(data=d, size=-delta)
                        else:
                            # Open new position
                            self.buy(data=d, size=target_size)
                            if self.params.printlog:
                                self.log(f"BUY {d._name} @ {d.close[0]:.2f} (size: {target_size})")
    
    def log(self, txt, dt=None):
        """Logging function"""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} - {txt}')


class DualMomentumStrategy(bt.Strategy):
    """
    Dual momentum (absolute + relative):
    1. Only hold assets with positive absolute momentum (returns > 0)
    2. Among positive assets, hold top N by relative momentum
    3. If no assets have positive momentum, go to cash
    """
    
    params = dict(
        lookback=60,           # Momentum lookback (60 days)
        top_n=2,               # Hold top N
        rebalance_days=21,     # Rebalance monthly
        printlog=False
    )
    
    def __init__(self):
        self.day_counter = 0
        self.rebalance_day = 0
        self.momentum = {}
        
        for d in self.datas:
            self.momentum[d] = bt.ind.ROC(d.close, period=self.params.lookback)
    
    def prenext(self):
        self.next()
    
    def next(self):
        self.day_counter += 1
        
        if self.day_counter < self.rebalance_day:
            return
        
        self.rebalance_day = self.day_counter + self.params.rebalance_days
        
        # Get all assets with POSITIVE momentum
        positive_momentum = []
        for d in self.datas:
            if len(d) < self.params.lookback + 10:
                continue
            
            mom = self.momentum[d][0]
            if mom > 0:  # Only consider assets trending UP
                positive_momentum.append((d, mom, d._name))
        
        # Sort by momentum
        positive_momentum.sort(key=lambda x: x[1], reverse=True)
        
        # Hold top N with positive momentum
        if len(positive_momentum) > 0:
            top_assets = set([d for d, score, name in positive_momentum[:self.params.top_n]])
        else:
            top_assets = set()  # Go to cash if nothing is trending up
        
        # Close positions not in top
        for d in self.datas:
            pos = self.getposition(d)
            if pos and d not in top_assets:
                self.close(data=d)
        
        # Equal weight top assets
        if len(top_assets) > 0:
            target_pct = 1.0 / len(top_assets)
            
            for d in top_assets:
                pos = self.getposition(d)
                target_value = self.broker.getvalue() * target_pct
                target_size = int(target_value / d.close[0])
                
                if target_size > 0:
                    if pos:
                        delta = target_size - pos.size
                        if abs(delta) > target_size * 0.1:  # Rebalance if >10% off
                            if delta > 0:
                                self.buy(data=d, size=delta)
                            else:
                                self.sell(data=d, size=-delta)
                    else:
                        self.buy(data=d, size=target_size)
    
    def log(self, txt, dt=None):
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} - {txt}')


class BuyAndHoldUniverse(bt.Strategy):
    """
    Simple buy-and-hold: Buy equal weight at start, hold forever
    """
    
    params = dict(
        printlog=False
    )
    
    def __init__(self):
        self.rebalanced = False
    
    def prenext(self):
        self.next()
    
    def next(self):
        if self.rebalanced:
            return
        
        # Buy equal weight of all assets
        n_assets = len(self.datas)
        if n_assets == 0:
            return
        
        target_pct = 1.0 / n_assets
        
        for d in self.datas:
            target_value = self.broker.getvalue() * target_pct
            target_size = int(target_value / d.close[0])
            
            if target_size > 0:
                self.buy(data=d, size=target_size)
                if self.params.printlog:
                    self.log(f"BUY & HOLD {d._name} @ {d.close[0]:.2f} (size: {target_size})")
        
        self.rebalanced = True
    
    def log(self, txt, dt=None):
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} - {txt}')

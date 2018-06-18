
# slice - .get()
myslice = self.my_sma.get(ago=-1, size=10)

# spread - ()
sma0 = btind.SMA(self.data0, period=15)  # 15 days sma
sma1 = btind.SMA(self.data1, period=5)  # 5 weeks sma
self.buysig = sma0 > sma1()

# bt.And
sell_sig = bt.And(check1, check2)

# bt.If
high_or_low = bt.If(sma > self.data.close, self.data.low, self.data.high)

# RSI Model Prediction
This aims to help to predict the best buying and selling point which based on the RSI.
When the index drops below 25, which means the market is on oversold.
Instead, when it exceeds 70, the market is on overbought.
By knowing this condition, first, the system will catch all the stock information on yahoo finance.
Then, followed the factor that we set, it will automatically pick all the potential profitable stock to you.
When you choose the stock that you want, you might consider when to sell, that's when you could apply for another system that I created that allow you to put in the stock you owned whether to decide sell it or not. 

# MACD Model Prediction
When the MACD value is above the signal period, it means that the market now is in an undervalue state, thus, the system will show this kind of stocks as a buying signal.
Instead, when the MACD value is below the signal period, the market is in an overvalue state, the system will suggest you to sell.

*why we pick 9 as signal period indicator?*
 
In the calculation of the MACD indicator, the period of the signal line is usually set to 9. This value is chosen based on experience and widespread application, and does not have a strict mathematical derivation. Here are some logical considerations for using 9 as the signal line period:

* Market Cycles: Stock markets typically experience short-term and long-term cyclical fluctuations. Selecting 9 as the signal line period can better capture these periodic changes and generate corresponding trading signals.
* Smoothing effect: The purpose of the signal line is to smooth the MACD value to reduce noise and misleading signals. An exponential moving average (EMA) with a period of 9 provides a moderate smoothing effect without being too lagging or overly responsive to price changes.
* Historical performance: In practice, the MACD indicator with a period of 9 has been widely used and verified. Many traders and analysts have found that this setup performs well on historical data and is able to generate reliable trading signals.
* Ease of observation: Choosing 9 as the signal line period can make the chart of the MACD indicator clearer and easier to read. A shorter period may cause the signal line to fluctuate too frequently, while a longer period may cause the signal line to react too slowly.
* Default Settings: In many technical analysis software and trading platforms, the default signal line period of the MACD indicator is set to 9. This makes this setup a common choice for easy communication and comparison between traders.

However, it should be noted that 9 is not an absolutely optimal value. Different markets, assets, and trading styles may require adjustments to signal line cycles. Traders can try different cycle settings based on their own experience and backtest results to find the parameters that best suit their strategy.
In short, it is a common practice to use 9 as the signal line period in the MACD indicator. This choice takes into account factors such as market cycle, smoothing effect, and historical performance. But traders should also remain flexible and make appropriate adjustments and optimizations based on specific circumstances.

# KDJ Model Prediction
To pick the buyable stock from KDJ model, the system will detect the K value, D value and J value. Once the K value acrosses the D value from the bottom and J value is bigger than the buying threshold, this will trigger the buying mechanism.
Instead, the K value acrosses the D value from the top and J value is smaller than the selling threshold, this will trigger the selling mechanism.

# Volume Model Prediction
The way we choose to buy or sell the stock, could also base on the volume of the transaction. Once the volume been increased 1.5 times than usual average volume, we take this as a buying point, the system will pick this kind of stock that recommend you to buy. 
Instead, once the volume been decreased 0.5 times than the average, we will list the stock as sellable.

*Warning: The system is still on early stage, many things will be fixed, so don't tend to rely on too much.*

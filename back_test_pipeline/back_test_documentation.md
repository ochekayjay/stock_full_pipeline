# 📊 Back test table result for NVIDIA and APPLE (April 2024 - August 2026)

The four tables below were spun off the stock-tracker data pipeline, giving quantitative valuations on the efficacy of the trading strategy implemented across the 2 years 4 months span from April 2024 to August 2026. 
----
The backtest was operationed here with the starting capital of $10,000. The trading strategy only trades on stocks that have attained some level of stability which in this case are stocks of which in the past 3 or more years have only been undulating between the near_record_high bucket (bucket/category with the highest value bounds) and higher range bucket (bucket/category with the second highest value bounds). Two unique tables per stock here helps display the decision made by the trader in relation to the best/worst case scenario decisions when purchasing a stock in 'Purchasing data breakdown' table and when retrieving your accrued interest in 'Sales data breakdown' table. Its also important to note that the mental model for the strategy utilized here is that, a stock is purchased only when it descends into the higher_range (relatively lower bucket) and stays there for a minimum of 2 days, and a share is sold only when the stock value has broken into the near_record_high (relatively, upper bucket) and its selling price is higher than the price for which it was bought (this is to neutralize the damaging impact on the bucket logic when stocks breaks into newer record highs or lows in the run). Further informations are shared successively. 
----
The tables covers two different stocks namely : 
- Nvidia
- Apple
And 2 different table case scenarios for each stock :
- **Purchasing data breakdown** : This includes critical decisions that a trader would have made within that bucket streak relative to the decision the trader actually made in regards to buying shares. For instance, it checks the drawdown in percentage between the amount the trader bought his shares at and the minimum value the stock recorded within that streak, the date when both events took place are also registered for traders and quants to judge trading trajectories by.
- **Sales data breakdown** : This includes critical decisions that a trader would have made within that streak period relative to the decision the trader actually made in regards to selling shares. For instance it checks the potential profit increment in percentage between the value the trader sold his stocks at and the value highest value the stock recorded in that streak window

For Purchasing Data breakdown we have the following columns
- **index**: The row index identifying the record.
- **purchased_date**: The date the stock was bought.
- **purchased_price** : The price the stock was bought at.
- **min_window_price** : The minimum value the stock recorded within that particular streak in the higher_range bucket.
- **min_price_date** : The date the stock recorded **min_window_price** . 
- **max_window_price** : The maximum value the stock recorded within that particular streak in the higher_range bucket.
- **max_price_date** : The date the stock recorded **max_window_price** .
- **drawdown_%** : Percentage of the difference between **purchased_price** and **min_window_price** divided by **purchased_price** .

For Sales Data breakdown we have the following columns
- **index**: The row index identifying the record.
- **sale_date**: The date the stock was sold.
- **sale_price** : The price the stock was sold at.
- **min_window_sale** : The minimum price the shares at hand would have been sold within that particular streak in the near_record_high bucket.
- **min_sale_date** : The date this selling price **min_window_sale** was recorded. 
- **max_window_sale** : The maximum value the shares at hand would have been  sold within that particular streak in the near_record_high bucket.
- **max_sale_date** : The date this selling price **max_window_sale** was recorded.
- **potential_increment %** : Percentage of the difference between **max_window_sale** and **sale_price** divided by **sale_price** .



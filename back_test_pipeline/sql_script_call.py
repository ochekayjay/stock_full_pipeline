back_test_query = """WITH distilled_table AS (
	SELECT id,
		   stock_valuation_date,
		   stock,
		   close_value 
	FROM stock_data.stock_live_table
),
full_join AS
(SELECT dt.stock AS stock,
	   dt.stock_valuation_date AS stock_valuation_date,
	   dt.close_value AS close_value,
	   hls.highest_lowest_valuation_key AS highest_lowest_valuation_key,
	   hls.start_date AS start_date,
	   hls.end_date AS end_date,
	   hls.day_length AS day_length
	   FROM distilled_table dt
JOIN stock_data.highest_lowest_stock_metric hls
ON dt.stock = hls.stock AND
dt.stock_valuation_date >= hls.start_date
AND dt.stock_valuation_date <= hls.end_date
)



SELECT stock,
       stock_valuation_date,
       close_value,
       MIN(stock_valuation_date) OVER (PARTITION BY stock,start_date ORDER BY stock_valuation_date ) AS start_date,
	   MAX(stock_valuation_date) OVER (PARTITION BY stock,start_date ORDER BY stock_valuation_date ) AS end_date,
       MIN(close_value) OVER (PARTITION BY stock,start_date ORDER BY stock_valuation_date ) AS maximum_close,
	   MAX(close_value) OVER (PARTITION BY stock,start_date ORDER BY stock_valuation_date ) AS minimum_close,
	   highest_lowest_valuation_key,
	   day_length
FROM full_join
"""


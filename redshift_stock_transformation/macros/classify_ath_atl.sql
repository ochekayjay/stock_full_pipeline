{% macro classify_ath_atl(stock_value,maximum_value, minimum_value) %}
    CASE
		WHEN maximum_value = minimum_value
			THEN 'mid_range'
		WHEN (stock_value - minimum_value)/(maximum_value-minimum_value) <= 0.20
			THEN 'near_record_low'
		WHEN (stock_value - minimum_value)/(maximum_value-minimum_value) <= 0.40
			THEN 'lower_range'
		WHEN (stock_value - minimum_value)/(maximum_value-minimum_value) <= 0.60
			THEN 'mid_range'
		WHEN (stock_value - minimum_value)/(maximum_value-minimum_value) <= 0.87
			THEN 'higher_range'
		ELSE
			'near_record_high'
	END 
{% endmacro %}
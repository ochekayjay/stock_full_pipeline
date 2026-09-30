{% macro classify_moving_average_crossover(short_avg_col, long_avg_col) %}
    CASE
        WHEN {{ short_avg_col }} > {{ long_avg_col }} THEN 'bullish_alignment'
        ELSE 'bearish_alignment'
    END
{% endmacro %}
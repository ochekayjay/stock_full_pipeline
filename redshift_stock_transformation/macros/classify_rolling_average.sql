{% macro classify_rolling_average(close_col, ninety_avg_col, ninety_stddev_col) %}
    CASE
        WHEN {{ close_col }} < {{ ninety_avg_col }} - {{ ninety_stddev_col }} THEN 'below'
        WHEN {{ close_col }} > {{ ninety_avg_col }} + {{ ninety_stddev_col }} THEN 'above'
        ELSE 'within'
    END
{% endmacro %}
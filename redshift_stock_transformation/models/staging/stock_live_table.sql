
{{ config( materialized='incremental',
    unique_key=['stock', 'stock_valuation_date'],
    incremental_strategy='merge') }}


WITH aapl_ds AS (
	SELECT "DATE"::date as stock_valuation_date,
			
			'AAPL' AS stock,
			NULLIF(Close_AAPL,'')::NUMERIC(12,4) as close_value,
			NULLIF(High_AAPL,'')::NUMERIC(12,4) AS high_value,
			NULLIF(Low_AAPL,'')::NUMERIC(12,4) AS low_value,
			NULLIF(Open_AAPL,'')::NUMERIC(12,4) AS open_value,
			NULLIF(Volume_AAPL,'')::NUMERIC(18,0) AS volume_value
	FROM {{ source('raw', 'stock_staging_table') }}
    {% if is_incremental() %}
    where "Date"::date > (COALESCE((select max(stock_valuation_date) from {{ this }}  where stock = 'AAPL'),'1900-01-01'::date))
    {% endif %}
),

nvda_ds AS (
	SELECT "DATE"::date as stock_valuation_date,
			'NVDA' AS stock,
			NULLIF(Close_NVDA,'')::NUMERIC(12,4) AS close_value,
			NULLIF(High_NVDA,'')::NUMERIC(12,4) AS high_value,
			NULLIF(Low_NVDA,'')::NUMERIC(12,4) AS low_value,
			NULLIF(Open_NVDA,'')::NUMERIC(12,4) AS open_value,
			NULLIF(Volume_NVDA,'')::NUMERIC(18,0) AS volume_value
	FROM {{ source('raw', 'stock_staging_table') }}
    {% if is_incremental() %}
    where "Date"::date > (COALESCE((select max(stock_valuation_date) from {{ this }} where stock = 'NVDA'),'1900-01-01'::date))
    {% endif %}
)


SELECT ({{ dbt.hash("stock_valuation_date::text || '-' || stock::text") }}) AS id,* FROM aapl_ds
UNION ALL
SELECT ({{ dbt.hash("stock_valuation_date::text || '-' || stock::text") }}) AS id,* FROM nvda_ds


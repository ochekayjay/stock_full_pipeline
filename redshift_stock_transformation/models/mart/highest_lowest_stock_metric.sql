-- depends_on: {{ ref('stock_last_snapshot_table') }}
-- depends_on: {{ ref('central_query_for_ephemeral') }}


{{ config( materialized='incremental',
    unique_key=['stock','start_date'],
    incremental_strategy='merge'
    )
    }}


{% if is_incremental() %}

 {% set target_count_query %}
        SELECT COUNT(*) FROM {{ this }}
		LIMIT 5
 {% endset %}

 {% set target_count = run_query(target_count_query) %}


  {% if target_count.columns[0].values()[0] == 0 %}

        WITH one_shot_call AS
		(
		SELECT
			stock::TEXT,
			highest_lowest_valuation,
			MIN(stock_valuation_date)::date AS start_date,
			MAX(stock_valuation_date)::date AS end_date,
			DATEDIFF(day, MIN(stock_valuation_date), MAX(stock_valuation_date)) + 1 AS day_length
		FROM {{ref('central_query_for_ephemeral')}}
		GROUP BY stock,high_low_streak_run,highest_lowest_valuation
		ORDER BY stock,start_date
		)

		SELECT ({{ dbt.hash("os.start_date::text || '-' || os.stock::text") }}) AS id,
			os.stock AS stock,
			hlv.id AS highest_lowest_valuation_key,
			os.start_date AS start_date,
			os.end_date AS end_date,
			os.day_length AS day_length
		FROM one_shot_call os JOIN
		{{ source('raw', 'highest_lowest_valuation_dim') }} hlv
		ON os.highest_lowest_valuation = hlv.bucket_name

    {% else %}

        WITH prev_avg_stock_table AS (
			SELECT *
			FROM {{ this }}
			WHERE end_date < 
			( SELECT main_date - '1 DAY'::INTERVAL FROM
			(SELECT MAX(stock_valuation_date) as main_date FROM {{ ref('stock_last_snapshot_table') }} 
			) f ) 
		),
		trailing_stock_table AS (
			SELECT *
			FROM {{ this }}

			 WHERE end_date =
			(
			SELECT MAX(main_date) AS main_date FROM (SELECT CASE
				WHEN EXTRACT(DOW FROM stock_valuation_date) = 1
						THEN DATEADD(day, -3, stock_valuation_date)
				ELSE
						DATEADD(day, -1, stock_valuation_date)
			END AS main_date 
			FROM {{ ref('stock_last_snapshot_table') }}
			) f
			GROUP BY main_date
		)
		),

		-- SELECT * FROM trailing_stock_table

		snapshot_with_bucket_id AS (
			SELECT stock_valuation_date,
				stock,
				stock_value,
				highest_lowest_valuation
				,hlv.id AS highest_lowest_valuation_id FROM 
			{{ ref('stock_last_snapshot_table') }} sls
			JOIN {{ source('raw', 'highest_lowest_valuation_dim') }} hlv
			ON sls.highest_lowest_valuation = hlv.bucket_name
		),

	
		matching_days AS (
		SELECT 
				({{ dbt.hash("ts.start_date::text || '-' || ts.stock::text") }}) AS id,
				ts.stock AS stock,
				ts.highest_lowest_valuation_key AS highest_lowest_valuation,
				ts.start_date AS start_date,
				CASE
				WHEN EXTRACT(DOW FROM ts.end_date) = 5
						THEN DATEADD(day, 3, ts.end_date)
				ELSE
						DATEADD(day, 1, ts.end_date)
				END AS end_date,
				CASE
				WHEN EXTRACT(DOW FROM ts.end_date) = 5
						THEN DATEDIFF(day,ts.start_date,ts.end_date +  '4 DAY'::INTERVAL)
				ELSE
						DATEDIFF(day,ts.start_date,ts.end_date +  '2 DAY'::INTERVAL)
				END AS day_length 
		FROM trailing_stock_table ts
		JOIN snapshot_with_bucket_id swb
		ON ts.stock = swb.stock
		AND ts.highest_lowest_valuation_key = swb.highest_lowest_valuation_id
		),
		unmatching_days AS (
            SELECT
                ({{ dbt.hash("ts.start_date::text || '-' || ts.stock::text") }}) AS id,
                ts.stock AS stock,
                ts.highest_lowest_valuation_key AS highest_lowest_valuation,
                ts.start_date AS start_date,
                ts.end_date AS end_date,
                ts.day_length AS day_length
            FROM trailing_stock_table ts
            JOIN snapshot_with_bucket_id swb
                ON ts.stock = swb.stock
                AND ts.highest_lowest_valuation_key <> swb.highest_lowest_valuation_id

            UNION ALL

            SELECT
                ({{ dbt.hash("swb.stock_valuation_date::text || '-' || ts.stock::text") }}) AS id,
                ts.stock AS stock,
                swb.highest_lowest_valuation_id AS highest_lowest_valuation,
                swb.stock_valuation_date AS start_date,
                swb.stock_valuation_date AS end_date,
                1 AS day_length
            FROM trailing_stock_table ts
            JOIN snapshot_with_bucket_id swb
                ON ts.stock = swb.stock
                AND ts.highest_lowest_valuation_key <> swb.highest_lowest_valuation_id
        ),

		final_table AS (
			SELECT * FROM matching_days
			UNION ALL
			SELECT * FROM unmatching_days
		)

		SELECT ({{ dbt.hash("ft.start_date::text || '-' || ft.stock::text") }}) AS id,
			ft.stock AS stock,
			hlv.id AS highest_lowest_valuation_key,
			ft.start_date AS start_date,
			ft.end_date AS end_date,
			ft.day_length AS day_length
		FROM final_table ft JOIN
		{{ source('raw', 'highest_lowest_valuation_dim') }} hlv
		ON ft.highest_lowest_valuation = hlv.id

  {% endif %}



{% else %}

WITH one_shot_call AS
(
SELECT
	stock::TEXT,
	highest_lowest_valuation,
	MIN(stock_valuation_date)::date AS start_date,
	MAX(stock_valuation_date)::date AS end_date,
	DATEDIFF(day, MIN(stock_valuation_date), MAX(stock_valuation_date)) + 1 AS day_length
FROM {{ref('central_query_for_ephemeral')}}
GROUP BY stock,high_low_streak_run,highest_lowest_valuation
ORDER BY stock,start_date
)

SELECT ({{ dbt.hash("os.start_date::text || '-' || os.stock::text") }}) AS id,
	   os.stock AS stock,
	   hlv.id AS highest_lowest_valuation_key,
	   os.start_date AS start_date,
	   os.end_date AS end_date,
	   os.day_length AS day_length
FROM one_shot_call os JOIN
{{ source('raw', 'highest_lowest_valuation_dim') }} hlv
ON os.highest_lowest_valuation = hlv.bucket_name



{% endif %}
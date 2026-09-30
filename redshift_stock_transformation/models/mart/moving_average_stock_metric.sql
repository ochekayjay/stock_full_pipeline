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
			moving_avg_comparison,
			MIN(stock_valuation_date)::date AS start_date,
			MAX(stock_valuation_date)::date AS end_date,
			DATEDIFF(day, MIN(stock_valuation_date), MAX(stock_valuation_date)) + 1 AS day_length
		FROM {{ref('central_query_for_ephemeral')}}
		GROUP BY stock,moving_avg_streak_run,moving_avg_comparison
		ORDER BY stock,start_date
		)

		SELECT ({{ dbt.hash("os.start_date::text || '-' || os.stock::text") }}) AS id,
			os.stock AS stock,
			mac.id AS moving_average_valuation_key,
			os.start_date AS start_date,
			os.end_date AS end_date,
			os.day_length AS day_length
		FROM one_shot_call os JOIN
		{{ source('raw', 'moving_avg_comparison_dim') }} mac
		ON os.moving_avg_comparison = mac.bucket_name

    {% else %}


			WITH prev_avg_stock_table AS (
				SELECT *
				FROM {{ this }}
				WHERE end_date < 
				( SELECT main_date - '1 DAY'::INTERVAL FROM
				(SELECT MAX(stock_valuation_date) AS main_date FROM {{ ref('stock_last_snapshot_table') }} 
				) f ) 
			),

			
			trailing_stock_table AS (
				SELECT *
				FROM {{ this }}
				WHERE end_date = 
				( SELECT main_date - '1 DAY'::INTERVAL FROM
				(SELECT MAX(stock_valuation_date) AS main_date FROM {{ ref('stock_last_snapshot_table') }} 
				) f ) 
			),

			snapshot_with_bucket_id AS (
			SELECT stock_valuation_date,
				stock,
				stock_value,
				moving_avg_comparison
				,mac.id AS moving_average_valuation_id FROM 
			{{ ref('stock_last_snapshot_table') }}  sls
			JOIN {{ source('raw', 'moving_avg_comparison_dim') }} mac
			ON sls.moving_avg_comparison = mac.bucket_name
		),

	
		matching_days AS (
		SELECT 
				({{ dbt.hash("ts.start_date::text || '-' || ts.stock::text") }}) AS id,
				ts.stock AS stock,
				ts.moving_average_valuation_key AS moving_avg_comparison,
				ts.start_date AS start_date,
				ts.end_date + '1 DAY'::INTERVAL AS end_date,
				DATEDIFF(day,ts.start_date,ts.end_date +'1 DAY'::INTERVAL) AS day_length 
		FROM trailing_stock_table ts
		JOIN snapshot_with_bucket_id swb
		ON ts.stock = swb.stock
		AND ts.moving_average_valuation_key = swb.moving_average_valuation_id
		),

		unmatching_days AS (
            SELECT
                ({{ dbt.hash("ts.start_date::text || '-' || ts.stock::text") }}) AS id,
                ts.stock AS stock,
                ts.moving_average_valuation_key AS moving_avg_comparison,
                ts.start_date AS start_date,
                ts.end_date AS end_date,
                ts.day_length AS day_length
            FROM trailing_stock_table ts
            JOIN snapshot_with_bucket_id swb
                ON ts.stock = swb.stock
                AND ts.moving_average_valuation_key <> swb.moving_average_valuation_id

            UNION ALL

            SELECT
                ({{ dbt.hash("swb.stock_valuation_date::text || '-' || ts.stock::text") }}) AS id,
                ts.stock AS stock,
                swb.moving_average_valuation_id AS moving_avg_comparison,
                swb.stock_valuation_date AS start_date,
                swb.stock_valuation_date AS end_date,
                1  AS day_length
            FROM trailing_stock_table ts
            JOIN snapshot_with_bucket_id swb
                ON ts.stock = swb.stock
                AND ts.moving_average_valuation_key <> swb.moving_average_valuation_id
        ),

		final_table AS ( 
		SELECT * FROM matching_days
		UNION ALL
		SELECT * FROM unmatching_days
		)

			SELECT ({{ dbt.hash("ft.start_date::text || '-' || ft.stock::text") }}) AS id,
				ft.stock AS stock,
				mac.id AS moving_average_valuation_key,
				ft.start_date AS start_date,
				ft.end_date AS end_date,
				ft.day_length AS day_length
			FROM final_table ft JOIN
			{{ source('raw', 'moving_avg_comparison_dim') }} mac
			ON ft.moving_avg_comparison = mac.id

	{% endif %}



{% else %}

	WITH one_shot_call AS
	(
	SELECT
		stock::TEXT,
		moving_avg_comparison,
		MIN(stock_valuation_date)::date AS start_date,
		MAX(stock_valuation_date)::date AS end_date,
		DATEDIFF(day, MIN(stock_valuation_date), MAX(stock_valuation_date)) + 1 AS day_length
	FROM {{ref('central_query_for_ephemeral')}}
	GROUP BY stock,moving_avg_streak_run,moving_avg_comparison
	ORDER BY stock,start_date
	)

	SELECT ({{ dbt.hash("os.start_date::text || '-' || os.stock::text") }}) AS id,
		os.stock AS stock,
		mac.id AS moving_average_valuation_key,
		os.start_date AS start_date,
		os.end_date AS end_date,
		os.day_length AS day_length
	FROM one_shot_call os JOIN
	{{ source('raw', 'moving_avg_comparison_dim') }} mac
	ON os.moving_avg_comparison = mac.bucket_name



{% endif %}
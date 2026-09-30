WITH factless_tables AS (SELECT end_date
FROM {{ ref('stock_average_metric') }}
ORDER BY end_date DESC
WHERE stock = 'NVDA'
LIMIT 1
),

SELECT * FROM
{{ ref('stock_live_table') }} slt
CROSS JOIN factless_tables ft
WHERE slt.stock_valuation_date > ft.end_date

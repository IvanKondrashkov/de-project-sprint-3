DELETE FROM staging.user_order_log AS uol
WHERE uol.date_time::DATE = '{{ds}}';
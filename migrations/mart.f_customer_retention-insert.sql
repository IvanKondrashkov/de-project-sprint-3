WITH
    customers AS
        (SELECT *
         FROM mart.f_sales
         JOIN mart.d_calendar ON f_sales.date_id = d_calendar.date_id
         WHERE DATE_PART('week', '{{ds}}'::DATE) = week_of_year),
    new_customers AS
        (SELECT DISTINCT
             customer_id
         FROM customers
         WHERE status = 'shipped'
         GROUP BY customer_id
         HAVING COUNT(*) = 1),
    returning_customers AS
        (SELECT DISTINCT
             customer_id
         FROM customers
         WHERE status = 'shipped'
         GROUP BY customer_id
         HAVING COUNT(*) > 1),
    refunded_customers AS
        (SELECT DISTINCT
             customer_id
         FROM customers
         WHERE status = 'refunded'
         GROUP BY customer_id
         HAVING COUNT(*) >= 1),
    new_customers_revenue AS
        (SELECT DISTINCT
             customer_id,
             SUM(payment_amount) AS total_amount
         FROM customers
         WHERE status = 'shipped'
         GROUP BY customer_id
         HAVING COUNT(*) = 1),
    returning_customers_revenue AS
        (SELECT DISTINCT
             customer_id,
             SUM(payment_amount) AS total_amount
         FROM customers
         WHERE status = 'shipped'
         GROUP BY customer_id
         HAVING count(*) > 1),
    customers_refunded AS
        (SELECT DISTINCT
             customer_id,
             SUM(quantity) AS total_quantity
         FROM customers
         WHERE status = 'refunded'
         GROUP BY customer_id
         HAVING COUNT(*) >= 1)

INSERT INTO mart.f_customer_retention(new_customers_count, returning_customers_count, refunded_customers_count, period_name, period_id, item_id, new_customers_revenue, returning_customers_revenue, customers_refunded)
SELECT
    SUM(nc.customer_id) AS new_customers_count,
    SUM(retc.customer_id) AS returning_customers_count,
    SUM(refc.customer_id) AS refunded_customers_count,
    'weekly' AS period_name,
    EXTRACT(WEEK FROM uol.date_time::DATE) AS period_id,
    uol.item_id AS item_id,
    SUM(ncr.total_amount) AS new_customers_revenue,
    SUM(rcr.total_amount) AS returning_customers_revenue,
    SUM(cr.total_quantity) AS customers_refunded
FROM staging.user_order_log AS uol
JOIN new_customers AS nc ON uol.customer_id = nc.customer_id
JOIN returning_customers AS retc ON uol.customer_id = retc.customer_id
JOIN refunded_customers AS refc ON uol.customer_id = refc.customer_id
JOIN new_customers_revenue AS ncr ON uol.customer_id = ncr.customer_id
JOIN returning_customers_revenue AS rcr ON uol.customer_id = rcr.customer_id
JOIN customers_refunded AS cr ON uol.customer_id = cr.customer_id
GROUP BY period_id, item_id;
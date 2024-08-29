CREATE TABLE IF NOT EXISTS mart.f_customer_retention(
    id                          SERIAL,         -- идентификатор.
    new_customers_count         INT,            -- кол-во новых клиентов (тех, которые сделали только один заказ за рассматриваемый промежуток времени).
    returning_customers_count   INT,            -- кол-во вернувшихся клиентов (тех, которые сделали только несколько заказов за рассматриваемый промежуток времени).
    refunded_customers_count    INT,            -- кол-во клиентов, оформивших возврат за рассматриваемый промежуток времени.
    period_name                 VARCHAR(6),     -- weekly.
    period_id                   BIGINT,         -- идентификатор периода (номер недели или номер месяца).
    item_id                     BIGINT,         -- идентификатор категории товара.
    new_customers_revenue       NUMERIC(10, 2), -- доход с новых клиентов.
    returning_customers_revenue NUMERIC(10, 2), -- доход с вернувшихся клиентов.
    customers_refunded          INT,            -- количество возвратов клиентов.
    PRIMARY KEY (id)
);

DELETE FROM mart.f_customer_retention
WHERE period_id = DATE_PART('week', '{{ds}}'::DATE);
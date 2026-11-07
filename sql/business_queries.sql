-- ============================================================================
-- TechBazaar retail sales: business questions in SQL (SQLite 3.25+)
-- Table: sales (see sql/schema.sql). Run all with:  python src/load_and_query_sql.py
--
-- Conventions
--   billed revenue = SUM(total_amount)          (matches the Excel / Power BI KPI sheet)
--   net sales      = SUM(quantity * unit_price) (the base that profit is defined on)
--   margin %       = SUM(profit) / SUM(net_sales) * 100   (weighted; never AVG of row %)
--   1 lakh = 1e5, 1 crore (Cr) = 1e7
--
-- Fixes vs. the first version of these queries
--   * margins were AVG(profit_margin_pct): an unweighted row average on a column that divides
--     profit (net-sales based) by total_amount -> replaced with a weighted, same-base margin;
--   * the monthly YoY query divided by 1,000,000 but labelled the result "lakh" (1 lakh = 100,000);
--   * "festival vs rest" compared 2 months of revenue with 10 months -> now per-month averages;
--   * discount buckets "1-10%" merged the 5% and 10% levels -> each actual level is shown.
-- Each query starts with "-- name: <file_name>" so the runner can save it to outputs/sql/.
-- ============================================================================


-- name: q01_yearly_kpis_yoy
-- Q1. How did the business do each year, and are we growing?
WITH y AS (
    SELECT year,
           COUNT(*)                    AS orders,
           COUNT(DISTINCT customer_id) AS customers,
           SUM(total_amount)           AS billed_revenue,
           SUM(net_sales)              AS net_sales,
           SUM(profit)                 AS profit
    FROM sales
    GROUP BY year
)
SELECT year,
       orders,
       customers,
       ROUND(billed_revenue / 1e7, 2)                         AS billed_revenue_cr,
       ROUND(net_sales / 1e7, 2)                              AS net_sales_cr,
       ROUND(profit / 1e7, 2)                                 AS profit_cr,
       ROUND(profit * 100.0 / net_sales, 2)                   AS margin_pct,
       ROUND(billed_revenue / orders, 0)                      AS avg_order_value,
       ROUND((billed_revenue / LAG(billed_revenue) OVER (ORDER BY year) - 1) * 100, 2) AS billed_revenue_yoy_pct,
       ROUND((profit / LAG(profit) OVER (ORDER BY year) - 1) * 100, 2)                 AS profit_yoy_pct,
       ROUND((orders * 1.0 / LAG(orders) OVER (ORDER BY year) - 1) * 100, 2)           AS orders_yoy_pct
FROM y
ORDER BY year;


-- name: q02_monthly_trend
-- Q2. Monthly trend: month-over-month change, 3-month moving average and same-month-last-year growth.
WITH m AS (
    SELECT year_month, year, month,
           COUNT(*)          AS orders,
           SUM(total_amount) AS billed,
           SUM(net_sales)    AS net
    FROM sales
    GROUP BY year_month, year, month
)
SELECT year_month,
       orders,
       ROUND(billed / 1e5, 1)                                                     AS billed_revenue_lakh,
       ROUND(net / 1e5, 1)                                                        AS net_sales_lakh,
       ROUND((billed / LAG(billed) OVER (ORDER BY year_month) - 1) * 100, 1)      AS billed_mom_pct,
       ROUND(AVG(billed) OVER (ORDER BY year_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) / 1e5, 1)
                                                                                  AS billed_3m_moving_avg_lakh,
       ROUND((billed / LAG(billed, 12) OVER (ORDER BY year_month) - 1) * 100, 1)  AS billed_yoy_pct
FROM m
ORDER BY year_month;


-- name: q03_festive_season_vs_rest
-- Q3. How big is the Oct-Nov festive season? Per-month averages so 2 months compare fairly with 10.
WITH m AS (
    SELECT year_month,
           MAX(is_festive_season) AS festive,
           COUNT(*)               AS orders,
           SUM(total_amount)      AS billed,
           SUM(net_sales)         AS net
    FROM sales
    GROUP BY year_month
)
SELECT CASE WHEN festive = 1 THEN 'Festive (Oct-Nov)' ELSE 'Rest of year' END AS period,
       COUNT(*)                              AS months,
       ROUND(AVG(orders), 0)                 AS avg_orders_per_month,
       ROUND(AVG(billed) / 1e5, 1)           AS avg_billed_revenue_per_month_lakh,
       ROUND(AVG(net) / 1e5, 1)              AS avg_net_sales_per_month_lakh,
       ROUND(SUM(billed) / SUM(orders), 0)   AS billed_aov,
       ROUND(SUM(net) / SUM(orders), 0)      AS net_aov
FROM m
GROUP BY period
ORDER BY period;


-- name: q04_category_mix
-- Q4. Which categories drive revenue and profit, and which are growing?
WITH c AS (
    SELECT category,
           SUM(total_amount)                                          AS billed,
           SUM(net_sales)                                             AS net,
           SUM(profit)                                                AS profit,
           SUM(quantity)                                              AS units,
           SUM(CASE WHEN year = 2022 THEN total_amount ELSE 0 END)   AS billed_2022,
           SUM(CASE WHEN year = 2023 THEN total_amount ELSE 0 END)   AS billed_2023
    FROM sales
    GROUP BY category
)
SELECT category,
       units,
       ROUND(billed / 1e7, 2)                               AS billed_revenue_cr,
       ROUND(billed * 100.0 / SUM(billed) OVER (), 1)       AS revenue_share_pct,
       ROUND(profit / 1e7, 2)                               AS profit_cr,
       ROUND(profit * 100.0 / SUM(profit) OVER (), 1)       AS profit_share_pct,
       ROUND(profit * 100.0 / net, 2)                       AS margin_pct,
       ROUND((billed_2023 / billed_2022 - 1) * 100, 1)      AS yoy_growth_pct,
       RANK() OVER (ORDER BY profit DESC)                   AS profit_rank
FROM c
ORDER BY billed DESC;


-- name: q05_top_products
-- Q5. Top 10 products by revenue, with their rank inside their own category.
WITH p AS (
    SELECT category, product_name,
           SUM(quantity)     AS units,
           SUM(total_amount) AS billed,
           SUM(net_sales)    AS net,
           SUM(profit)       AS profit
    FROM sales
    GROUP BY category, product_name
), ranked AS (
    SELECT *,
           RANK() OVER (ORDER BY billed DESC)                        AS overall_rank,
           RANK() OVER (PARTITION BY category ORDER BY billed DESC)  AS rank_in_category,
           billed * 100.0 / SUM(billed) OVER ()                      AS share
    FROM p
)
SELECT overall_rank, product_name, category, rank_in_category, units,
       ROUND(billed / 1e7, 2)          AS billed_revenue_cr,
       ROUND(share, 1)                 AS revenue_share_pct,
       ROUND(profit / 1e7, 2)          AS profit_cr,
       ROUND(profit * 100.0 / net, 2)  AS margin_pct
FROM ranked
WHERE overall_rank <= 10
ORDER BY overall_rank;


-- name: q06_city_performance
-- Q6. How does each city perform on revenue, customers, basket size, margin and growth?
SELECT city,
       COUNT(*)                                                         AS orders,
       COUNT(DISTINCT customer_id)                                      AS customers,
       ROUND(SUM(total_amount) / 1e7, 2)                                AS billed_revenue_cr,
       ROUND(SUM(total_amount) * 100.0 / SUM(SUM(total_amount)) OVER (), 1) AS revenue_share_pct,
       ROUND(AVG(total_amount), 0)                                      AS avg_order_value,
       ROUND(SUM(profit) * 100.0 / SUM(net_sales), 2)                   AS margin_pct,
       ROUND((SUM(CASE WHEN year = 2023 THEN total_amount END) /
              SUM(CASE WHEN year = 2022 THEN total_amount END) - 1) * 100, 1) AS yoy_growth_pct
FROM sales
GROUP BY city
ORDER BY SUM(total_amount) DESC;


-- name: q07_discount_vs_margin
-- Q7. Does discounting pay for itself? Margin, basket size and order mix at each discount level.
SELECT discount_pct,
       COUNT(*)                                                  AS orders,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)        AS order_share_pct,
       ROUND(AVG(quantity), 3)                                   AS avg_units_per_order,
       ROUND(SUM(net_sales) / 1e7, 2)                            AS net_sales_cr,
       ROUND(SUM(profit) / 1e7, 2)                               AS profit_cr,
       ROUND(SUM(profit) * 100.0 / SUM(net_sales), 2)            AS margin_pct,
       ROUND(SUM(base_price * quantity - net_sales) / 1e7, 2)    AS discount_given_cr
FROM sales
GROUP BY discount_pct
ORDER BY discount_pct;


-- name: q08_discount_depth_by_category
-- Q8. Which categories are discounted hardest, and what does that do to their margin?
SELECT category,
       ROUND(AVG(discount_pct), 2)                                            AS avg_discount_pct,
       ROUND(SUM(CASE WHEN discount_pct >= 15 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS deep_discount_order_pct,
       ROUND(SUM(base_price * quantity - net_sales) * 100.0 / SUM(base_price * quantity), 2) AS effective_discount_pct,
       ROUND(SUM(profit) * 100.0 / SUM(net_sales), 2)                         AS margin_pct
FROM sales
GROUP BY category
ORDER BY avg_discount_pct DESC;


-- name: q09_payment_mode
-- Q9. How do customers pay, and does payment mode change the basket?
SELECT payment_mode,
       COUNT(*)                                             AS orders,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)   AS order_share_pct,
       ROUND(AVG(total_amount), 0)                          AS avg_order_value,
       ROUND(AVG(quantity), 3)                              AS avg_units_per_order,
       ROUND(SUM(CASE WHEN category IN ('Laptops', 'Televisions') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                                                            AS big_ticket_order_pct
FROM sales
GROUP BY payment_mode
ORDER BY orders DESC;


-- name: q10_payment_mode_by_city
-- Q10. Payment preference by city (share of each city's orders), as a pivot.
SELECT city,
       ROUND(SUM(payment_mode = 'UPI')         * 100.0 / COUNT(*), 1) AS upi_pct,
       ROUND(SUM(payment_mode = 'Credit Card') * 100.0 / COUNT(*), 1) AS credit_card_pct,
       ROUND(SUM(payment_mode = 'Debit Card')  * 100.0 / COUNT(*), 1) AS debit_card_pct,
       ROUND(SUM(payment_mode = 'Cash')        * 100.0 / COUNT(*), 1) AS cash_pct,
       ROUND(SUM(payment_mode = 'EMI')         * 100.0 / COUNT(*), 1) AS emi_pct
FROM sales
GROUP BY city
ORDER BY city;


-- name: q11_customer_repeat_and_retention
-- Q11. How many customers come back? Order-frequency distribution plus 2022 -> 2023 retention.
WITH cust AS (
    SELECT customer_id,
           COUNT(*)                                   AS orders,
           MAX(CASE WHEN year = 2022 THEN 1 ELSE 0 END) AS in_2022,
           MAX(CASE WHEN year = 2023 THEN 1 ELSE 0 END) AS in_2023
    FROM sales
    GROUP BY customer_id
)
SELECT 'customers'                                AS metric, COUNT(*) AS value FROM cust
UNION ALL
SELECT 'repeat customers (2+ orders)',            SUM(orders >= 2) FROM cust
UNION ALL
SELECT 'repeat rate %',                           ROUND(SUM(orders >= 2) * 100.0 / COUNT(*), 1) FROM cust
UNION ALL
SELECT 'customers with 1 order',                  SUM(orders = 1) FROM cust
UNION ALL
SELECT 'customers with 2-4 orders',               SUM(orders BETWEEN 2 AND 4) FROM cust
UNION ALL
SELECT 'customers with 5-7 orders',               SUM(orders BETWEEN 5 AND 7) FROM cust
UNION ALL
SELECT 'customers with 8+ orders',                SUM(orders >= 8) FROM cust
UNION ALL
SELECT 'avg orders per customer',                 ROUND(AVG(orders), 2) FROM cust
UNION ALL
SELECT '2022 customers retained in 2023 %',       ROUND(SUM(in_2022 AND in_2023) * 100.0 / SUM(in_2022), 1) FROM cust
UNION ALL
SELECT 'new customers in 2023 (not seen in 2022)', SUM(in_2023 AND NOT in_2022) FROM cust;


-- name: q12_rfm_segments
-- Q12. RFM segmentation (snapshot 2024-01-01): score Recency, Frequency, Monetary 1-5 with NTILE.
WITH base AS (
    SELECT customer_id,
           CAST(julianday('2024-01-01') - julianday(MAX(date)) AS INTEGER) AS recency_days,
           COUNT(*)                                                       AS frequency,
           SUM(total_amount)                                              AS monetary
    FROM sales
    GROUP BY customer_id
), scored AS (
    SELECT *,
           NTILE(5) OVER (ORDER BY recency_days DESC)          AS r,   -- most recent -> 5
           NTILE(5) OVER (ORDER BY frequency, monetary)        AS f,   -- ties broken by spend
           NTILE(5) OVER (ORDER BY monetary)                   AS m
    FROM base
), seg AS (
    SELECT *,
           CASE
               WHEN r >= 4 AND f >= 4             THEN '1 Champions'
               WHEN r >= 3 AND f >= 3             THEN '2 Loyal'
               WHEN r >= 4 AND f <= 2             THEN '3 Recent / Promising'
               WHEN r <= 2 AND f >= 3             THEN '4 At risk'
               WHEN r <= 2 AND f <= 2             THEN '6 Hibernating'
               ELSE                                    '5 Need attention'
           END AS segment
    FROM scored
)
SELECT segment,
       COUNT(*)                                                 AS customers,
       ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)       AS customer_share_pct,
       ROUND(AVG(recency_days), 0)                              AS avg_recency_days,
       ROUND(AVG(frequency), 2)                                 AS avg_orders,
       ROUND(AVG(monetary), 0)                                  AS avg_spend,
       ROUND(SUM(monetary) * 100.0 / SUM(SUM(monetary)) OVER (), 1) AS revenue_share_pct
FROM seg
GROUP BY segment
ORDER BY segment;


-- name: q13_top_customers
-- Q13. Top 10 customers by lifetime revenue, and how much of revenue the top 10% of customers hold.
WITH c AS (
    SELECT customer_id,
           COUNT(*)              AS orders,
           SUM(total_amount)     AS billed,
           SUM(profit)           AS profit,
           MIN(date)             AS first_order,
           MAX(date)             AS last_order,
           GROUP_CONCAT(DISTINCT city) AS cities
    FROM sales
    GROUP BY customer_id
), ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (ORDER BY billed DESC)     AS rnk,
           NTILE(10)    OVER (ORDER BY billed DESC)     AS decile,
           SUM(billed)  OVER ()                         AS total
    FROM c
)
SELECT rnk AS rank, customer_id, orders, cities, first_order, last_order,
       ROUND(billed / 1e5, 2)                 AS billed_revenue_lakh,
       ROUND(profit / 1e5, 2)                 AS profit_lakh,
       ROUND(billed * 100.0 / total, 3)       AS revenue_share_pct,
       ROUND((SELECT SUM(billed) FROM ranked WHERE decile = 1) * 100.0 / total, 1) AS top10pct_customers_revenue_share
FROM ranked
WHERE rnk <= 10
ORDER BY rnk;

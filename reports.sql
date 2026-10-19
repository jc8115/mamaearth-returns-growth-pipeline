-- Mamaearth Relational Reporting Suite
-- Task 3: Analytical SQL Queries with Exact Output Comments

-- ============================================================================
-- Report (a): Order totals
-- total_orders: 180 | total_revenue: 99860.20 | avg_order_value: 554.78
-- ============================================================================
SELECT 
    COUNT(*) AS total_orders,
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_revenue,
    ROUND(AVG(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS avg_order_value
FROM orders o
JOIN products p ON o.product_id = p.product_id;

-- ============================================================================
-- Report (b): COUNT(*) vs COUNT(column)
-- total_orders: 180 | rated_orders: 165 | unrated_orders: 15
-- ============================================================================
SELECT 
    COUNT(*) AS total_orders,
    COUNT(rating) AS rated_orders,
    COUNT(*) - COUNT(rating) AS unrated_orders
FROM orders;

-- ============================================================================
-- Report (c): LEFT JOIN with zero-match row & NOT IN confirmation
-- LEFT JOIN Result: C045 | Vihaan
-- NOT IN Result:    C045 | Vihaan
-- ============================================================================
SELECT 
    c.customer_id, 
    c.name
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name
HAVING COUNT(o.order_id) = 0;

SELECT 
    customer_id, 
    name
FROM customers
WHERE customer_id NOT IN (
    SELECT DISTINCT customer_id 
    FROM orders 
    WHERE customer_id IS NOT NULL
);

-- ============================================================================
-- Report (d): High Return Rate Cities (> 20%)
-- city: Jaipur    | total_orders: 19 | returned_orders: 8  | return_rate_pct: 42.1
-- city: Lucknow   | total_orders: 49 | returned_orders: 15 | return_rate_pct: 30.6
-- city: Bangalore | total_orders: 33 | returned_orders: 8  | return_rate_pct: 24.2
-- ============================================================================
SELECT 
    c.city,
    COUNT(o.order_id) AS total_orders,
    SUM(o.returned) AS returned_orders,
    ROUND(100.0 * SUM(o.returned) / COUNT(o.order_id), 1) AS return_rate_pct
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.city
HAVING return_rate_pct > 20.0
ORDER BY return_rate_pct DESC;

-- ============================================================================
-- Report (e): Ranking with ORDER BY + LIMIT/OFFSET
-- Tie-break comment: customer_id ASC guarantees deterministic pagination when total spend matches.
--
-- Top 5 (LIMIT 5):
-- C043 | Reyansh | 12920.00
-- C026 | Isha    | 8371.60
-- C008 | Meera   | 4564.60
-- C011 | Arjun   | 4111.00
-- C042 | Sanya   | 3785.00
--
-- Ranks 3 to 5 (LIMIT 3 OFFSET 2):
-- C008 | Meera   | 4564.60
-- C011 | Arjun   | 4111.00
-- C042 | Sanya   | 3785.00
-- ============================================================================
SELECT 
    c.customer_id,
    c.name,
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend
FROM orders o
JOIN products p ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 5;

SELECT 
    c.customer_id,
    c.name,
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS total_spend
FROM orders o
JOIN products p ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_id, c.name
ORDER BY total_spend DESC, c.customer_id ASC
LIMIT 3 OFFSET 2;

-- ============================================================================
-- Report (f): Three-table JOIN with Category Aggregation
-- Haircare     | 54 | 44956.10
-- Skincare     | 60 | 27346.00
-- Babycare     | 30 | 16805.00
-- PersonalCare | 36 | 10753.10
-- ============================================================================
SELECT 
    p.category,
    COUNT(o.order_id) AS order_count,
    ROUND(SUM(o.quantity * p.price * (1 - COALESCE(o.discount_pct, 0) / 100.0)), 2) AS category_revenue
FROM orders o
JOIN products p ON o.product_id = p.product_id
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY p.category
ORDER BY category_revenue DESC;

-- ============================================================================
-- Report (g): LIKE pattern match ('A%')
-- Returns exactly 10 rows:
-- C001, C003, C004, C011, C021, C030, C031, C036, C041, C044
-- ============================================================================
SELECT customer_id, name 
FROM customers 
WHERE name LIKE 'A%'
ORDER BY customer_id ASC;

-- ============================================================================
-- Report (h): DISTINCT acquisition sources
-- Ad | Organic | Referral | Social
-- ============================================================================
SELECT DISTINCT acquisition_source 
FROM customers 
ORDER BY acquisition_source ASC;

-- ============================================================================
-- Report (i): ALTER TABLE + UPDATE CASE Loyalty Tier
-- Gold   | 28
-- Silver | 17
-- ============================================================================
ALTER TABLE customers ADD COLUMN loyalty_tier VARCHAR(10);

UPDATE customers 
SET loyalty_tier = CASE 
    WHEN city_tier = 1 THEN 'Gold' 
    ELSE 'Silver' 
END;

SELECT loyalty_tier, COUNT(*) AS customer_count
FROM customers
GROUP BY loyalty_tier
ORDER BY loyalty_tier ASC;
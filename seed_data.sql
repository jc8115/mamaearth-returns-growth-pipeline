-- Mamaearth Seed Data Loader & Initialization
-- Task 2: CSV Data Ingestion & NULL Sanitization

-- In SQLite CLI:
-- .mode csv
-- .import --skip 1 data/customers.csv customers
-- .import --skip 1 data/products.csv products
-- .import --skip 1 data/orders.csv orders

-- Convert empty strings into SQL NULLs:
UPDATE orders SET discount_pct = NULL WHERE discount_pct = '';
UPDATE orders SET rating = NULL WHERE rating = '';

-- Verification queries:
-- SELECT COUNT(*) FROM customers; -- 45
-- SELECT COUNT(*) FROM products;  -- 16
-- SELECT COUNT(*) FROM orders;    -- 180
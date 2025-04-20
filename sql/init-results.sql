-- Create results table for processed orders
CREATE TABLE IF NOT EXISTS results (
    id SERIAL PRIMARY KEY,
    order_id INT UNIQUE NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    total DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    processed_at TIMESTAMP NOT NULL,
    CONSTRAINT fk_order FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- Create index for faster lookups
CREATE INDEX idx_results_customer_id ON results(customer_id);
CREATE INDEX idx_results_product_id ON results(product_id);
CREATE INDEX idx_results_status ON results(status);

-- Create view for order analytics
CREATE OR REPLACE VIEW order_analytics AS
SELECT
    product_id,
    COUNT(*) as total_orders,
    SUM(quantity) as total_quantity,
    SUM(total) as total_revenue,
    AVG(price) as avg_price
FROM results
GROUP BY product_id
ORDER BY total_revenue DESC;

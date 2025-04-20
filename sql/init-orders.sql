-- Enable replication for Debezium
ALTER SYSTEM SET wal_level = logical;
ALTER SYSTEM SET max_replication_slots = 10;
ALTER SYSTEM SET max_wal_senders = 5;
-- Create orders table
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create orders table
CREATE TABLE IF NOT EXISTS heart_beat (
    id numeric primary key,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

insert into heart_beat (id) values (1);
-- Create function to update timestamp
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for maintaining updated_at
CREATE TRIGGER update_orders_modtime
BEFORE UPDATE ON orders
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

-- Insert sample data
INSERT INTO orders (customer_id, product_id, quantity, price, status)
VALUES 
    ('CUST001', 'PROD100', 5, 29.99, 'PENDING'),
    ('CUST002', 'PROD200', 1, 99.99, 'PENDING'),
    ('CUST003', 'PROD300', 3, 15.50, 'PENDING'),
    ('CUST001', 'PROD400', 2, 49.95, 'PENDING'),
    ('CUST004', 'PROD100', 10, 29.99, 'PENDING');

-- Grant permissions needed for CDC
ALTER TABLE orders REPLICA IDENTITY FULL;

-- Create publication for the orders table
CREATE PUBLICATION orders_pub FOR TABLE orders;

-- Create a logical replication slot (uncomment if you want manual creation)
-- SELECT pg_create_logical_replication_slot('orders_slot', 'pgoutput');
-- SELECT * FROM pg_replication_slots;

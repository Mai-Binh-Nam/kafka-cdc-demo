# kafka-cdc-demo
Streaming đơn hàng (orders) từ PostgreSQL thông qua Debezium → Kafka → Consumer (Node.js/Python) để enrich thêm thông tin khách hàng từ Redis và lưu kết quả vào PostgreSQL khác.

# Kafka CDC Demo

## Project Overview

This project demonstrates a real-time Change Data Capture (CDC) pipeline using:
- **PostgreSQL** as the source database
- **Debezium** for change data capture
- **Apache Kafka** as the message broker
- **Kafka Connect** to stream database changes
- **Python Consumer** to process the data stream
- **Redis** for caching and fast lookups
- All services are containerized using Docker

## Architecture

1. PostgreSQL database contains an `orders` table
2. Debezium monitors the PostgreSQL transaction log for changes
3. Changes are published to Kafka topics
4. A Python consumer processes these events in real-time
5. Processed results are stored in the `results` table and cached in Redis

## Project Structure

```
kafka-cdc-demo/
├── docker-compose.yml       # Docker services configuration
├── connect/
│   └── postgres-connector.json  # Debezium connector configuration
├── consumer/
│   ├── main.py              # Python consumer application
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Consumer container definition
├── redis/
│   └── preload.json         # Redis initial configuration
└── sql/
    ├── init-orders.sql      # SQL for orders table and sample data
    └── init-results.sql     # SQL for results table
```

## How to Run

1. Make sure you have Docker and Docker Compose installed
2. Clone this repository
3. Start the services:
   ```bash
   docker-compose up -d
   ```
4. Check that all services are running:
   ```bash
   docker-compose ps
   ```

## Testing the Pipeline

1. Connect to PostgreSQL and insert a new order:
   ```sql
   INSERT INTO orders (customer_id, product_id, quantity, price, status)
   VALUES ('CUST005', 'PROD500', 7, 19.99, 'PENDING');
   ```

2. Check the results table to see the processed order:
   ```sql
   SELECT * FROM results WHERE customer_id = 'CUST005';
   ```

3. Verify data in Redis:
   ```bash
   docker exec -it redis redis-cli HGETALL "order:6"
   ```

## Monitoring

- Kafka Connect UI: http://localhost:8083
- Kafka UI: http://localhost:8085
- PostgreSQL: postgres:5432 (user: postgres, password: postgres)
- Replication Slot: 
  ```sql
   SELECT slot_name, 
   active, 
   restart_lsn, 
   confirmed_flush_lsn, 
   pg_current_wal_lsn(), 
   pg_current_wal_lsn() - restart_lsn AS lag
   FROM pg_replication_slots;
  ```
- Redis: redis:6379

## Troubleshooting

- Check connector status: `curl http://kafka-connect:8083/connectors/orders-connector/status`
- View Kafka topics: `docker exec -it kafka kafka-topics --bootstrap-server kafka:9092 --list`
- Consumer logs: `docker-compose logs -f consumer`
- Kafka Connect logs: `docker-compose logs -f kafka-connect`

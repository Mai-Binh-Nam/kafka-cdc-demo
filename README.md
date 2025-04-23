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

## Improvement Recommendations for Kafka CDC
### Scalability Improvements
- Multi-node Kafka cluster: Configure Kafka for high availability with multiple brokers and appropriate replication factors
- Partition strategy: Implement key-based partitioning for the orders topic to ensure ordered processing while allowing horizontal scaling
- Stateful processing: Add Kafka Streams for stateful processing of order events (e.g., aggregations by customer)

### Monitoring and Observability
- Prometheus & Grafana: Add metrics collection and dashboards for system health monitoring
- Distributed tracing: Implement OpenTelemetry to trace events through the entire pipeline
- Log aggregation: Add centralized logging with ELK stack or Loki
- Alerts: Configure alerts for critical system events and performance degradation

### Error Handling and Resilience
- Dead Letter Queue processing: Create a dedicated consumer for the dlq-errors topic with retry logic and notification capabilities
- Circuit breaker pattern: Implement circuit breakers for external dependencies
- Idempotent consumers: Enhance consumer logic to ensure exactly-once processing semantics

### Security Enhancements
- Authentication: Add SASL/SCRAM authentication for Kafka
- Encryption: Enable TLS for all services
- Data protection: Implement field-level encryption for sensitive customer data
- Authorization: Configure ACLs for Kafka topics and Schema Registry

### Data Transformation and Enrichment Pipeline
- Stream processing: Add Kafka Streams or KSQL for real-time analytics
- Data enrichment: Integrate with external APIs to enhance order data with product/customer details
- Complex event processing: Detect patterns like suspicious order activity
- Multiple destination systems: Add connectors for data warehouses (Snowflake/BigQuery) or analytics platforms

### Schema Evolution and Compatibility
- Avro serialization: Use Schema Registry with Avro instead of JSON for better type safety and evolution
- Compatibility rules: Configure Schema Registry with compatibility checks (BACKWARD, FORWARD)
- Schema versioning: Implement a strategy for handling schema changes

### User Interface and Visualization
- Real-time dashboard: Build a React or Vue.js dashboard showing live order statistics
- Order visualization: Create visualizations for order flow through the system
- Admin panel: Add administrative controls for connector management and system configuration

### Testing and Development Workflow
- Integration testing: Add comprehensive integration tests with Docker Compose profiles
- Chaos testing: Simulate service failures to verify resilience
- CI/CD pipeline: Configure GitHub Actions workflow for automated testing and deployment
- Local development: Add dev mode with smaller resource requirements

### Business Features
- Notification service: Add email/SMS notifications for order status changes
- Anomaly detection: Implement ML-based anomaly detection for unusual order patterns
- Business metrics: Calculate and expose key business metrics (order volume, processing time)
- Audit trail: Maintain a complete audit trail of all data changes
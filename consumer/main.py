#!/usr/bin/env python3
import json
import os
import time
from datetime import datetime
import logging

from confluent_kafka import Consumer, KafkaError
import redis
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('kafka-cdc-consumer')

# Get environment variables
KAFKA_BOOTSTRAP_SERVERS = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', 5432))
POSTGRES_USER = os.environ.get('POSTGRES_USER', 'postgres')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'postgres')
POSTGRES_DB = os.environ.get('POSTGRES_DB', 'orders')

# Kafka topic (derived from Debezium connector configuration)
KAFKA_TOPIC = 'postgres.public.orders'

def get_postgres_connection():
    """Create a connection to PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            dbname=POSTGRES_DB
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        raise

def get_redis_connection():
    """Create a connection to Redis."""
    try:
        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )
        return r
    except redis.RedisError as e:
        logger.error(f"Error connecting to Redis: {e}")
        raise

def process_order(order_data):
    """Process an order and save results to PostgreSQL and Redis."""
    try:
        # Get order data
        order_id = order_data.get('id')
        customer_id = order_data.get('customer_id')
        product_id = order_data.get('product_id')
        quantity = order_data.get('quantity', 0)
        price = order_data.get('price', 0.0)
        status = order_data.get('status', 'PENDING')
        
        if not order_id:
            logger.warning(f"Missing order_id in data: {order_data}")
            return
        
        # Calculate total (as an example processing step)
        total = quantity * price
        
        # Create result data
        result = {
            'order_id': order_id,
            'customer_id': customer_id,
            'product_id': product_id,
            'quantity': quantity,
            'price': price,
            'total': total,
            'status': status,
            'processed_at': datetime.now().isoformat()
        }
        
        # Save to PostgreSQL
        pg_conn = get_postgres_connection()
        cursor = pg_conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO results (order_id, customer_id, product_id, quantity, price, total, status, processed_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (order_id) 
            DO UPDATE SET
                status = EXCLUDED.status,
                processed_at = EXCLUDED.processed_at
            """,
            (
                order_id, customer_id, product_id, quantity, 
                price, total, status, result['processed_at']
            )
        )
        pg_conn.commit()
        cursor.close()
        pg_conn.close()
        
        # Save to Redis for fast lookup
        redis_conn = get_redis_connection()
        redis_key = f"order:{order_id}"
        redis_conn.hset(redis_key, mapping=result)
        
        # Also maintain a list of recent orders (limit to 100)
        redis_conn.lpush("recent_orders", json.dumps(result))
        redis_conn.ltrim("recent_orders", 0, 99)
        
        logger.info(f"Processed order {order_id} - Status: {status}, Total: {total}")
        
    except Exception as e:
        logger.error(f"Error processing order: {e}")
        raise

def main():
    """Main consumer function."""
    logger.info("Starting Kafka CDC Consumer")
    
    # Configure Kafka consumer
    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'order-processing-group',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,
    }
    
    consumer = Consumer(conf)
    consumer.subscribe([KAFKA_TOPIC])
    
    try:
        while True:
            # Poll for messages
            msg = consumer.poll(timeout=1.0)
            
            if msg is None:
                continue
                
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.info(f"Reached end of partition: {msg.topic()}/{msg.partition()}")
                else:
                    logger.error(f"Kafka error: {msg.error()}")
            else:
                try:
                    # Parse message value
                    value = json.loads(msg.value().decode('utf-8'))
                    logger.debug(f"Received message: {value}")
                    
                    # Process the order
                    process_order(value)
                    
                    # Commit offset after successful processing
                    consumer.commit(msg)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding JSON: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
    finally:
        # Close down consumer
        consumer.close()
        logger.info("Consumer closed")

if __name__ == "__main__":
    # Wait for Kafka and other services to be ready
    time.sleep(10)
    
    # Start consumer
    main()

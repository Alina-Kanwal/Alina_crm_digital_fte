# Kafka Production Setup Guide

## Option 1: Aiven Kafka (Recommended for Production)

### Prerequisites
- Aiven account (free tier available)
- Aiven CLI installed: `pip install aiven-client`

### Setup Steps

1. **Authenticate with Aiven:**
```bash
avn user login
# Follow the prompts to authenticate
```

2. **Create FREE Kafka Service:**
```bash
avn service create digital-fte-kafka \
  --service-type kafka \
  --cloud aws-ap-southeast-1 \
  --plan startup-1-2 \
  --project <your-project-name>
```

3. **Get Service Details:**
```bash
avn service get digital-fte-kafka
```

4. **Download SSL Certificates:**
```bash
mkdir -p certs
avn service user-download-kafka-ac --project <your-project-name> digital-fte-kafka
```

5. **Create Topics:**
```bash
avn service topic-create digital-fte-kafka customer_inquiries \
  --partitions 3 --replication-factor 2

avn service topic-create digital-fte-kafka agent_responses \
  --partitions 3 --replication-factor 2
```

6. **Update .env with Kafka Details:**
```bash
KAFKA_BOOTSTRAP_SERVERS=<your-kafka-brokers>
KAFKA_SECURITY_PROTOCOL=SSL
KAFKA_SSL_CAFILE=./certs/ca.pem
KAFKA_SSL_CERTFILE=./certs/service.cert
KAFKA_SSL_KEYFILE=./certs/service.key
```

## Option 2: Confluent Cloud

### Prerequisites
- Confluent Cloud account (free tier available)
- Confluent CLI installed

### Setup Steps

1. **Login to Confluent Cloud:**
```bash
confluent login
```

2. **Create Kafka Cluster:**
```bash
confluent kafka cluster create digital-fte-kafka \
  --cloud aws \
  --region us-east-1 \
  --type basic
```

3. **Create API Key:**
```bash
confluent api-key create --resource <cluster-id>
```

4. **Create Topics:**
```bash
confluent kafka topic create customer_inquiries --partitions 3
confluent kafka topic create agent_responses --partitions 3
```

5. **Update .env with Kafka Details**

## Option 3: Local Development (Not Recommended for Production)

### Using Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3'
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

Start Kafka:
```bash
docker-compose up -d
```

## Verification

After setting up Kafka, verify connectivity:

```bash
# Test with Python
python -c "
from kafka import KafkaProducer, KafkaConsumer
import os

producer = KafkaProducer(
    bootstrap_servers=os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
    acks='all'
)
producer.send('customer_inquiries', key=b'test', value=b'{"test": "message"}')
producer.flush()
print('Kafka producer working!')
"
```

## Production Considerations

1. **Security:** Use SSL/TLS for all production Kafka connections
2. **High Availability:** Use at least 3 brokers with replication factor of 2
3. **Monitoring:** Set up Kafka metrics and monitoring
4. **Backup:** Configure Kafka topic replication for disaster recovery
5. **Performance:** Tune Kafka parameters based on your workload

## Troubleshooting

### Connection Issues
- Check firewall rules allow Kafka port access (9092, 9093 for SSL)
- Verify SSL certificates are valid and paths are correct
- Ensure security groups allow inbound traffic

### Topic Issues
- Verify topics exist: `avn service topic-list <service-name>`
- Check topic configurations: `avn service topic-get <service-name> <topic-name>`

### Performance Issues
- Monitor consumer lag
- Check broker resource utilization
- Review partition distribution

## Local Development Setup — SAM + Docker

Run the entire SiteForge stack locally without AWS credentials.

### Prerequisites

```bash
# Install SAM CLI
brew install aws-sam-cli

# Install Docker and Docker Compose
# macOS: brew install docker docker-compose
# Linux: sudo apt install docker.io docker-compose
# Windows: Install Docker Desktop

# Verify installations
sam --version
docker --version
docker-compose --version
```

### Quick Start

#### 1. Start the stack

```bash
cd /workspace/siteforge/infra/local
docker-compose up -d
```

This starts:
- **DynamoDB Local**: http://localhost:8000
- **LocalStack** (SNS/SQS/SSM): http://localhost:4566
- **Lambda API**: http://localhost:3001

#### 2. Wait for services to be ready

```bash
# Check DynamoDB health
curl http://localhost:8000/

# Check API readiness (wait ~10s for initialization)
curl http://localhost:3001/api/config
```

#### 3. Test the API

```bash
# Public endpoint
curl http://localhost:3001/api/config

# Create user
curl -X POST http://localhost:3001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!",
    "firstName": "Test",
    "lastName": "User"
  }'

# List users (admin endpoint)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:3001/api/admin/users
```

### Managing Local Data

#### View DynamoDB tables

```bash
# List all items in a table
aws dynamodb scan \
  --endpoint-url http://localhost:8000 \
  --table-name siteforge-serenity-therapy \
  --region us-east-1

# Query a specific user
aws dynamodb get-item \
  --endpoint-url http://localhost:8000 \
  --table-name siteforge-serenity-therapy \
  --key '{"pk": {"S": "ADMIN#admin@example.com"}, "sk": {"S": "USER"}}' \
  --region us-east-1
```

#### Seed test data

```bash
# Reset and reseed database
docker exec siteforge-dynamodb-local-1 bash -c \
  "rm -rf /tmp/data/* && /opt/java/openjdk/bin/java -jar DynamoDBLocal.jar -sharedDb -dbPath /tmp/data"

# Then run init script
bash infra/local/init.sh
```

#### Clear everything

```bash
docker-compose down -v
docker-compose up -d
# Services will auto-initialize on startup
```

### Debugging

#### View API logs

```bash
docker-compose logs -f api
```

#### Test Lambda locally without API

```bash
cd apps/api
sam build --use-container
sam local invoke SiteForgeApi -e test-event.json
```

#### Check LocalStack resources

```bash
# List SNS topics
aws sns list-topics \
  --endpoint-url http://localhost:4566 \
  --region us-east-1

# List SSM parameters
aws ssm describe-parameters \
  --endpoint-url http://localhost:4566 \
  --region us-east-1
```

### Environment Variables

For frontend, set:

```bash
# .env.local in frontend directory
NEXT_PUBLIC_API_URL=http://localhost:3001/api
NEXT_PUBLIC_DOMAIN=localhost:3000
```

### Common Issues

**Q: "Connection refused" on http://localhost:3001**

A: Wait 10-15 seconds for Lambda to initialize after `docker-compose up`. Check logs:
```bash
docker-compose logs api
```

**Q: DynamoDB table not found**

A: Manually create it:
```bash
bash infra/local/init.sh
```

**Q: Port 3001 already in use**

A: Change in docker-compose.yaml:
```yaml
ports:
  - "3002:8000"  # or any available port
```

Then use http://localhost:3002 for API calls.

**Q: Can't authenticate — JWT validation fails**

A: Local JWT secret is auto-generated. Check logs for secret:
```bash
docker-compose logs api | grep "JWT"
```

### Stop & Clean Up

```bash
# Stop all services but keep data
docker-compose stop

# Restart
docker-compose start

# Destroy everything (including data)
docker-compose down -v
```

### Next Steps

1. **Frontend dev**: `npm run dev -w apps/frontend`
2. **Run tests**: `pytest apps/api/tests -v`
3. **Deploy to AWS**: Follow main README for CDK deployment

"""
Pytest configuration and fixtures for SiteForge API tests.
Uses moto to mock AWS services (DynamoDB, SSM).
"""
import os
import sys
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pytest
import boto3
from moto import mock_aws
import bcrypt

# Add parent directory to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock environment variables
os.environ["TABLE_NAME"] = "test-siteforge-table"
os.environ["SITE_ID"] = "test-site"
os.environ["DOMAIN"] = "test-site.local"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
os.environ["DEFAULT_LANG"] = "en"
os.environ["SENDER_NAME"] = "Test Site"
os.environ["BREVO_API_KEY"] = ""  # Empty for testing


@pytest.fixture(scope="session")
def aws_credentials():
    """Set AWS credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(autouse=True)
def mock_aws_context(aws_credentials):
    """Activate mock AWS for all tests."""
    with mock_aws():
        # Create DynamoDB table
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName=os.environ["TABLE_NAME"],
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"},
                {"AttributeName": "GSI1PK", "AttributeType": "S"},
                {"AttributeName": "GSI1SK", "AttributeType": "S"},
                {"AttributeName": "email", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "GSI1",
                    "KeySchema": [
                        {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                        {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "GSI2",
                    "KeySchema": [
                        {"AttributeName": "email", "KeyType": "HASH"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
        )
        
        # Create SSM parameters
        ssm = boto3.client("ssm", region_name="us-east-1")
        ssm.put_parameter(
            Name=f"/siteforge/{os.environ['SITE_ID']}/jwt_secret",
            Value=os.environ["JWT_SECRET"],
            Type="SecureString",
        )
        ssm.put_parameter(
            Name=f"/siteforge/{os.environ['SITE_ID']}/brevo_api_key",
            Value="sk_test_placeholder",  # Non-empty for testing
            Type="SecureString",
        )
        
        # Clear module cache to ensure mocking works
        import lib.db
        lib.db._resource = None
        
        yield


@pytest.fixture
def test_user_data():
    """Create test user data."""
    return {
        "email": "user@test.local",
        "firstName": "Test",
        "lastName": "User",
        "phone": "+1 (555) 000-0000",
        "password": "SecurePassword123!",
    }


@pytest.fixture
def test_admin_data():
    """Create test admin data."""
    return {
        "email": "admin@test.local",
        "firstName": "Admin",
        "lastName": "User",
        "phone": "+1 (555) 000-0001",
        "password": "AdminPassword123!",
    }


@pytest.fixture
def seeded_user(mock_aws_context):
    """Create a seeded user in the database."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from lib.db import put_item
    
    user_id = str(uuid.uuid4())
    test_user_data = {
        "email": "user@test.local",
        "firstName": "Test",
        "lastName": "User",
        "phone": "+1 (555) 000-0000",
        "password": "SecurePassword123!",
    }
    pw_hash = bcrypt.hashpw(test_user_data["password"].encode(), bcrypt.gensalt()).decode()
    now = datetime.utcnow().isoformat() + "Z"
    
    user = {
        "PK": f"USER#{user_id}",
        "SK": "PROFILE",
        "userId": user_id,
        "email": test_user_data["email"],
        "firstName": test_user_data["firstName"],
        "lastName": test_user_data["lastName"],
        "phone": test_user_data["phone"],
        "passwordHash": pw_hash,
        "verified": True,
        "role": "user",
        "createdAt": now,
        "updatedAt": now,
    }
    
    put_item(user)
    return {**user, "plainPassword": test_user_data["password"]}


@pytest.fixture
def seeded_admin(mock_aws_context):
    """Create a seeded admin user in the database."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from lib.db import put_item
    
    test_admin_data = {
        "email": "admin@test.local",
        "firstName": "Admin",
        "lastName": "User",
        "phone": "+1 (555) 000-0001",
        "password": "AdminPassword123!",
    }
    user_id = str(uuid.uuid4())
    pw_hash = bcrypt.hashpw(test_admin_data["password"].encode(), bcrypt.gensalt()).decode()
    now = datetime.utcnow().isoformat() + "Z"
    
    user = {
        "PK": f"USER#{user_id}",
        "SK": "PROFILE",
        "userId": user_id,
        "email": test_admin_data["email"],
        "firstName": test_admin_data["firstName"],
        "lastName": test_admin_data["lastName"],
        "phone": test_admin_data["phone"],
        "passwordHash": pw_hash,
        "verified": True,
        "role": "admin",
        "createdAt": now,
        "updatedAt": now,
    }
    
    put_item(user)
    return {**user, "plainPassword": test_admin_data["password"]}


@pytest.fixture
def seeded_service(mock_aws_context):
    """Create a seeded service in the database."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from lib.db import put_item
    
    service_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat() + "Z"
    
    service = {
        "PK": f"SERVICE#{service_id}",
        "SK": "DETAIL",
        "serviceId": service_id,
        "name": {
            "en": "Test Service",
            "es": "Servicio de Prueba",
        },
        "description": {
            "en": "A test service",
            "es": "Un servicio de prueba",
        },
        "durationMinutes": 50,
        "active": True,
        "createdAt": now,
        "updatedAt": now,
    }
    
    put_item(service)
    return service


@pytest.fixture
def test_token(seeded_user):
    """Generate a valid JWT token for a test user."""
    import jwt
    from datetime import datetime, timedelta, timezone
    
    payload = {
        "userId": seeded_user["userId"],
        "email": seeded_user["email"],
        "role": "user",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc),
    }
    
    token = jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")
    return token


@pytest.fixture
def admin_token(seeded_admin):
    """Generate a valid JWT token for a test admin."""
    import jwt
    from datetime import datetime, timedelta, timezone
    
    payload = {
        "userId": seeded_admin["userId"],
        "email": seeded_admin["email"],
        "role": "admin",
        "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        "iat": datetime.now(timezone.utc),
    }
    
    token = jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")
    return token


@pytest.fixture
def api_request_handler():
    """Return the main API handler function."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from main import handler
    return handler


def create_request_event(
    method: str,
    path: str,
    body: dict = None,
    query: dict = None,
    headers: dict = None,
    auth_token: str = None,
) -> dict:
    """Helper to create an API Gateway v2 event."""
    event = {
        "requestContext": {
            "http": {
                "method": method,
                "path": path,
            },
        },
        "headers": headers or {},
        "queryStringParameters": query or None,
        "body": json.dumps(body) if body else None,
    }
    
    if auth_token:
        event["headers"]["Authorization"] = f"Bearer {auth_token}"
        event["headers"]["Cookie"] = f"auth_token={auth_token}"
    
    return event


@pytest.fixture
def make_request(api_request_handler):
    """Fixture to make API requests in tests."""
    def _make_request(
        method: str,
        path: str,
        body: dict = None,
        query: dict = None,
        headers: dict = None,
        auth_token: str = None,
    ) -> dict:
        event = create_request_event(method, path, body, query, headers, auth_token)
        response = api_request_handler(event, {})
        
        # Parse response body
        if isinstance(response.get("body"), str):
            try:
                response["body"] = json.loads(response["body"])
            except (json.JSONDecodeError, TypeError):
                pass
        
        return response
    
    return _make_request


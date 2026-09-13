"""Pytest fixtures for Phase 0-13 testing with database isolation."""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.base import Base
from app.models.models import User, Organization
from app.security.auth import hash_password, create_access_token
from fastapi.testclient import TestClient
from app.main import app


# Use SQLite in-memory for tests (faster, isolated)
TEST_DATABASE_URL = "sqlite:///:memory:"


class UserWithHeaders:
    """Wrapper to support both object and dict-like access to User for testing."""
    
    def __init__(self, user, token, headers, organization=None):
        self._user = user
        self._token = token
        self._headers = headers
        self._organization = organization
    
    def __getattr__(self, name):
        """Support object attribute access."""
        if name in ('_user', '_token', '_headers', '_organization'):
            return object.__getattribute__(self, name)
        if name == 'headers':
            return object.__getattribute__(self, '_headers')
        if name == 'token':
            return object.__getattribute__(self, '_token')
        if name == 'organization':
            return object.__getattribute__(self, '_organization')
        if name == 'user':
            return object.__getattribute__(self, '_user')
        # Delegate to user object
        return getattr(object.__getattribute__(self, '_user'), name)
    
    def __getitem__(self, key):
        """Support dict-like access."""
        if key == 'headers':
            return self._headers
        if key == 'token':
            return self._token
        if key == 'organization':
            return self._organization
        if key == 'user':
            return self._user
        return getattr(self._user, key)


@pytest.fixture(scope="function")
def test_db():
    """Create test database and session for each test.
    
    Creates fresh in-memory SQLite database for each test with all tables.
    Automatically cleaned up after test.
    
    Yields:
        SQLAlchemy session connected to test database
    """
    # Create in-memory SQLite engine
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Enable JSON1 extension for SQLite if available
    @event.listens_for(engine, "connect")
    def load_json(dbapi_conn, connection_record):
        """Load JSON extension for SQLite."""
        try:
            dbapi_conn.enable_load_extension(True)
            dbapi_conn.load_extension("json1")
            dbapi_conn.enable_load_extension(False)
        except Exception:
            # JSON1 not available, SQLite will handle JSON as TEXT
            pass
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    yield db
    
    # Cleanup
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_client(test_db):
    """FastAPI test client with dependency override for database.
    
    Provides TestClient that uses test database instead of production.
    
    Args:
        test_db: Test database session from test_db fixture
        
    Yields:
        FastAPI TestClient
    """
    from app.db.base import get_db
    
    app.dependency_overrides[get_db] = lambda: test_db
    
    client = TestClient(app)
    yield client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user_officer(test_db):
    """Create officer user for testing.
    
    Args:
        test_db: Test database session
        
    Returns:
        UserWithHeaders wrapper supporting both object and dict-like access
    """
    org = Organization(legal_name="GeM Ministry")
    test_db.add(org)
    test_db.flush()
    
    user = User(
        email="officer@gem.gov",
        password_hash=hash_password("officer123"),
        role="officer",
        organization_id=org.id,
    )
    test_db.add(user)
    test_db.commit()
    
    token = create_access_token(str(user.id), "officer", 60)
    headers = {"Authorization": f"Bearer {token}"}
    
    return UserWithHeaders(user, token, headers)


@pytest.fixture(scope="function")
def test_user_bidder(test_db):
    """Create bidder user for testing.
    
    Args:
        test_db: Test database session
        
    Returns:
        UserWithHeaders wrapper supporting both object and dict-like access
    """
    org = Organization(
        legal_name="Test Bidder Inc",
        gstin="22TEST0001H1Z0",
        pan="TESTPA1234A",
    )
    test_db.add(org)
    test_db.flush()
    
    user = User(
        email="bidder@test.com",
        password_hash=hash_password("password123"),
        role="bidder",
        organization_id=org.id,
    )
    test_db.add(user)
    test_db.commit()
    
    token = create_access_token(str(user.id), "bidder", 60)
    headers = {"Authorization": f"Bearer {token}"}
    
    return UserWithHeaders(user, token, headers, organization=org)


@pytest.fixture(scope="function")
def test_user_admin(test_db):
    """Create admin user for testing.
    
    Args:
        test_db: Test database session
        
    Returns:
        UserWithHeaders wrapper supporting both object and dict-like access
    """
    org = Organization(legal_name="GeM Admin")
    test_db.add(org)
    test_db.flush()
    
    user = User(
        email="admin@gem.gov",
        password_hash=hash_password("admin123"),
        role="admin",
        organization_id=org.id,
    )
    test_db.add(user)
    test_db.commit()
    
    token = create_access_token(str(user.id), "admin", 60)
    headers = {"Authorization": f"Bearer {token}"}
    
    return UserWithHeaders(user, token, headers)

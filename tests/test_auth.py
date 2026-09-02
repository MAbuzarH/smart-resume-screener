"""
Test file for Authentication functionality.
Tests user registration, login, logout, and authorization.
"""

import pytest
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash, check_password_hash


@pytest.fixture(autouse=True)
def cleanup_database():
    """
    Cleanup database before each test to avoid conflicts.
    """
    flask_app = create_app()
    with flask_app.app_context():
        # Clean up all users before each test
        User.query.delete()
        db.session.commit()
    yield
    # Cleanup after each test
    with flask_app.app_context():
        User.query.delete()
        db.session.commit()


def test_user_model_password_hashing():
    """
    Test that User model properly hashes passwords.
    """
    # Test password hashing
    password = "testpassword123"
    hashed = generate_password_hash(password)
    
    # Verify hash is not plain text
    assert hashed != password
    assert len(hashed) > 50  # Hashes should be significantly longer than passwords
    
    # Verify hash can be checked
    assert check_password_hash(hashed, password)
    assert not check_password_hash(hashed, "wrongpassword")


def test_user_creation():
    """
    Test that users can be created and stored correctly.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        user = User(
            full_name='Test User',
            email='test@example.com',
            role='applicant'
        )
        user.set_password('password123')
        
        db.session.add(user)
        db.session.commit()
        
        # Verify user was saved
        saved_user = User.query.filter_by(email='test@example.com').first()
        assert saved_user is not None
        assert saved_user.full_name == 'Test User'
        assert saved_user.role == 'applicant'
        assert saved_user.is_active == True
        assert saved_user.check_password('password123')
        assert not saved_user.check_password('wrongpassword')


def test_registration_duplicate_email():
    """
    Test that duplicate email registration is rejected.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        # Create first user
        user1 = User(
            full_name='Test User',
            email='test@example.com',
            role='applicant'
        )
        user1.set_password('password123')
        db.session.add(user1)
        db.session.commit()
        
        # Try to create duplicate
        with flask_app.test_client() as client:
            response = client.post('/register', data={
                'full_name': 'Another User',
                'email': 'test@example.com',
                'password': 'password123',
                'confirm_password': 'password123',
                'route': 'applicant'
            }, follow_redirects=False)
            
            # Should fail due to duplicate email
            assert response.status_code == 200
            assert b'already exists' in response.data.lower()


def test_login_valid_credentials():
    """
    Test that valid credentials allow login.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        # Create test user
        user = User(
            full_name='Test User',
            email='test@example.com',
            role='applicant'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Test login
        with flask_app.test_client() as client:
            response = client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            }, follow_redirects=False)
            
            # Should redirect after successful login
            assert response.status_code == 302


def test_login_invalid_credentials():
    """
    Test that invalid credentials are rejected.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        # Create test user
        user = User(
            full_name='Test User',
            email='test@example.com',
            role='applicant'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Test login with wrong password
        with flask_app.test_client() as client:
            response = client.post('/login', data={
                'email': 'test@example.com',
                'password': 'wrongpassword'
            }, follow_redirects=False)
            
            # Should stay on login page with error
            assert response.status_code == 200
            assert b'Invalid email or password' in response.data


def test_login_unknown_user():
    """
    Test that unknown email is rejected.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        response = client.post('/login', data={
            'email': 'unknown@example.com',
            'password': 'password123'
        }, follow_redirects=False)
        
        # Should stay on login page with error
        assert response.status_code == 200
        assert b'Invalid email or password' in response.data


def test_logout():
    """
    Test that logout clears the session.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        # Create test user
        user = User(
            full_name='Test User',
            email='test@example.com',
            role='applicant'
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        with flask_app.test_client() as client:
            # Login
            client.post('/login', data={
                'email': 'test@example.com',
                'password': 'password123'
            })
            
            # Logout
            response = client.get('/logout', follow_redirects=False)
            
            # Should redirect to home
            assert response.status_code == 302


def test_registration_applicant_role():
    """
    Test that applicant role can be registered.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        response = client.post('/register', data={
            'full_name': 'Test Applicant',
            'email': 'applicant@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'applicant'
        }, follow_redirects=False)
        
        # Should redirect to login after successful registration
        assert response.status_code == 302


def test_registration_employer_role():
    """
    Test that employer role can be registered.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        response = client.post('/register', data={
            'full_name': 'Test Employer',
            'email': 'employer@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'employer'
        }, follow_redirects=False)
        
        # Should redirect to login after successful registration
        assert response.status_code == 302


def test_protected_route_requires_login():
    """
    Test that protected routes redirect to login when not authenticated.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        # Try to access protected apply route without login
        response = client.get('/job/1/apply', follow_redirects=False)
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/login' in response.location


def test_password_validation():
    """
    Test that password validation works correctly.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        # Test password too short
        response = client.post('/register', data={
            'full_name': 'Test User',
            'email': 'test@example.com',
            'password': '123',  # Too short
            'confirm_password': '123',
            'role': 'applicant'
        }, follow_redirects=False)
        
        assert response.status_code == 200
        assert b'at least 6 characters' in response.data.lower() or b'six characters' in response.data.lower()


def test_password_mismatch():
    """
    Test that password mismatch is rejected.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        response = client.post('/register', data={
            'full_name': 'Test User',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'different123',
            'role': 'applicant'
        }, follow_redirects=False)
        
        assert response.status_code == 200
        assert b'do not match' in response.data.lower() or b'match' in response.data.lower()


def test_email_validation():
    """
    Test that invalid email is rejected.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        response = client.post('/register', data={
            'full_name': 'Test User',
            'email': 'invalid-email',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'applicant'
        }, follow_redirects=False)
        
        assert response.status_code == 200
        assert b'valid email' in response.data.lower()


def test_admin_role_not_public():
    """
    Test that public registration cannot create admin role.
    """
    flask_app = create_app()
    
    with flask_app.test_client() as client:
        # Try to register as admin via public form
        response = client.post('/register', data={
            'full_name': 'Test Admin',
            'email': 'admin@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'role': 'admin'
        }, follow_redirects=False)
        
        # Should be rejected or handled safely
        assert response.status_code == 200


def test_user_is_active_field():
    """
    Test that is_active field works correctly.
    """
    flask_app = create_app()
    
    with flask_app.app_context():
        user = User(
            full_name='Test User',
            email='test@example.com',
            role='applicant',
            is_active=False
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        
        # Verify is_active is False
        saved_user = User.query.get(user.id)
        assert saved_user.is_active == False
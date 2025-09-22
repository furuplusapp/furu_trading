# Furu AI Backend

FastAPI backend for the Furu AI trading platform with authentication, Celery, Redis, and PostgreSQL.

## Features

- **Authentication**: JWT-based authentication with email verification
- **User Management**: User registration, login, profile management
- **Email System**: Celery-powered email sending for verification and password reset
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis for session storage and Celery message broker
- **API Documentation**: Auto-generated OpenAPI/Swagger docs

## Tech Stack

- **FastAPI**: Modern, fast web framework
- **PostgreSQL**: Primary database
- **Redis**: Caching and message broker
- **Celery**: Background task processing
- **SQLAlchemy**: ORM
- **Alembic**: Database migrations
- **JWT**: Authentication tokens

## Quick Start

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL and Redis**:

   - Install PostgreSQL and create database `furu_db`
   - Install Redis

3. **Configure environment**:

   ```bash
   cp env.example .env
   # Edit .env with your database and email settings
   ```

4. **Run migrations**:

   ```bash
   alembic upgrade head
   ```

5. **Start the application**:

   ```bash
   # Terminal 1: Start FastAPI
   uvicorn app.main:app --reload

   # Terminal 2: Start Celery worker
   celery -A app.tasks.celery_app worker --loglevel=info
   ```

6. **Access the API**:
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/verify-email` - Verify email address
- `POST /api/v1/auth/resend-verification` - Resend verification email
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password

### Users

- `GET /api/v1/users/me` - Get current user info
- `PUT /api/v1/users/me` - Update current user
- `DELETE /api/v1/users/me` - Deactivate account

## Database Schema

### Users Table

- `id`: Primary key
- `email`: Unique email address
- `username`: Unique username
- `hashed_password`: Bcrypt hashed password
- `full_name`: User's full name
- `is_active`: Account status
- `is_verified`: Email verification status
- `plan`: User plan (free, pro, elite)
- `created_at`: Account creation timestamp
- `updated_at`: Last update timestamp
- `last_login`: Last login timestamp

### Email Verifications Table

- `id`: Primary key
- `user_id`: Foreign key to users
- `token`: Unique verification token
- `created_at`: Token creation timestamp
- `expires_at`: Token expiration timestamp
- `is_used`: Token usage status

### Password Resets Table

- `id`: Primary key
- `user_id`: Foreign key to users
- `token`: Unique reset token
- `created_at`: Token creation timestamp
- `expires_at`: Token expiration timestamp
- `is_used`: Token usage status

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Formatting

```bash
black .
isort .
```

## Production Deployment

1. **Set production environment variables**
2. **Use a production database** (AWS RDS, etc.)
3. **Use a production Redis instance** (AWS ElastiCache, etc.)
4. **Set up proper logging and monitoring**
5. **Use a reverse proxy** (Nginx)
6. **Set up SSL certificates**
7. **Configure email service** (SendGrid, AWS SES, etc.)
8. **Consider using Docker for production deployment**

## License

MIT License

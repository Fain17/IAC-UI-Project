# IAC UI Agent Backend

A FastAPI backend for managing EC2 instances and launch templates with user authentication, workflow management, and real-time token monitoring.

## Features

- 🔐 **Authentication & Authorization**: JWT-based authentication with refresh tokens
- 👥 **User Management**: Admin and regular user roles with permission levels
- 🔄 **Workflow Management**: Create, execute, and manage scripts (sh, playbook, terraform, aws, python, node)
- 🐳 **Sandboxed Execution**: Docker-based script execution with resource limits
- 📡 **Real-time Monitoring**: WebSocket-based token expiration monitoring
- 🔒 **Secure WebSocket (WSS)**: Support for secure WebSocket connections
- 🗄️ **Database**: LibSQL/SQLite for data persistence

## Quick Start

### Prerequisites

- Python 3.12+
- OpenSSL (for WSS support)
- Docker (for script execution)

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Generate SSL certificates for WSS**:
   ```bash
   python generate_ssl_certs.py
   ```

3. **Start the server**:
   ```bash
   python app/main.py
   ```

The server will start with WSS support if SSL certificates are found, otherwise it will start with regular HTTP/WS.

## WebSocket Configuration

### Secure WebSocket (WSS) - Recommended

The backend supports secure WebSocket connections using SSL/TLS certificates.

#### Frontend Connection (WSS):
```javascript
// Connect to secure WebSocket
const ws = new WebSocket(`wss://localhost:8000/ws/token-monitor?token=${accessToken}`);

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.call_refresh) {
        console.log("🔄 Token refresh needed!");
        console.log("Time remaining:", data.time_remaining_seconds, "seconds");
        // Handle token refresh
        refreshToken();
    }
};

ws.onopen = function() {
    console.log("✅ Secure WebSocket connected");
};

ws.onclose = function() {
    console.log("❌ WebSocket disconnected");
};
```

#### Regular WebSocket (WS) - Fallback:
```javascript
// Connect to regular WebSocket (if SSL not available)
const ws = new WebSocket(`ws://localhost:8000/ws/token-monitor?token=${accessToken}`);
```

### SSL Certificate Management

#### Development (Self-signed):
```bash
# Generate self-signed certificates
python generate_ssl_certs.py

# Certificates will be created in:
# - certs/key.pem (private key)
# - certs/cert.pem (certificate)
```

#### Production:
1. **Obtain SSL certificates** from a trusted CA (Let's Encrypt, etc.)
2. **Place certificates** in the `certs/` directory:
   - `certs/key.pem` - Private key
   - `certs/cert.pem` - Certificate
3. **Set environment variables** (optional):
   ```bash
   export SSL_KEYFILE=certs/key.pem
   export SSL_CERTFILE=certs/cert.pem
   ```

## Docker Deployment

### Development:
```bash
# Build and run with WSS support
docker-compose up --build
```

### Production:
```bash
# Run with nginx reverse proxy
docker-compose --profile production up --build
```

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login (returns access + refresh tokens)
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout (revoke session)
- `GET /auth/verify-token` - Verify token validity

### Workflows
- `GET /workflow/get-all-mappings` - Get all config mappings
- `POST /workflow/create-mapping` - Create new mapping
- `DELETE /workflow/delete-mapping` - Delete mapping
- `POST /workflow/workflows` - Create workflow
- `GET /workflow/workflows` - Get user workflows
- `DELETE /workflow/workflows/{id}` - Delete workflow
- `POST /workflow/workflows/{id}/execute` - Execute workflow

### Admin
- `GET /admin/users` - Get all users (admin only)
- `POST /admin/users` - Create user (admin only)
- `DELETE /admin/users/{id}` - Delete user (admin only)
- `PUT /admin/users/{id}/permissions` - Update user permissions (admin only)

### WebSocket
- `wss://localhost:8000/ws/token-monitor` - Token monitoring endpoint

## Environment Variables

```bash
# Database
LIBSQL_URL=file:data/database.db
LIBSQL_AUTH_TOKEN=

# JWT
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Cleanup
CLEANUP_INTERVAL_SECONDS=3600

# SSL (optional)
SSL_KEYFILE=certs/key.pem
SSL_CERTFILE=certs/cert.pem
```

## Security Features

- 🔐 **JWT Authentication** with configurable expiration (30 minutes default)
- 🔄 **Refresh Token Mechanism** for seamless token renewal (7 days default)
- 🛡️ **Password Hashing** using bcrypt
- 🔒 **HTTPS/WSS Support** with SSL/TLS encryption
- 🚫 **CORS Protection** with configurable origins
- 🧹 **Automatic Cleanup** of expired sessions and tokens (every hour)

## Token Monitoring

The WebSocket system monitors user tokens and automatically notifies the frontend when:
- Token expires in ≤ 60 seconds
- Sends `call_refresh: true` message to trigger token refresh

## Development

### Running Tests
```bash
# Add test commands here when implemented
```

### Code Style
```bash
# Add linting commands here when implemented
```

## License

[Add your license here] 
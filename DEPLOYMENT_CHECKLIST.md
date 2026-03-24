# Production Deployment Checklist

Complete this checklist before deploying to production.

## Pre-Deployment Review

### Code Quality

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Code style compliant: `flake8 services/ main.py`
- [ ] No debug statements in code
- [ ] No hardcoded credentials
- [ ] Error messages are user-friendly
- [ ] Logging is comprehensive

### Security

- [ ] DATABASE_URL uses strong password
- [ ] No credentials in .env.example
- [ ] HTTPS/TLS configured on reverse proxy
- [ ] CORS configured if needed
- [ ] Authentication implemented (JWT/OAuth2)
- [ ] Rate limiting configured
- [ ] Input validation in place
- [ ] SQL injection prevention verified
- [ ] File upload size limits enforced

### Performance

- [ ] Database indexes created
- [ ] Connection pooling configured
- [ ] Caching strategy defined
- [ ] Load testing completed
- [ ] Response times acceptable
- [ ] Resource usage monitored

### Documentation

- [ ] All endpoints documented
- [ ] API contract finalized
- [ ] Error codes documented
- [ ] Deployment instructions written
- [ ] Configuration documented
- [ ] Troubleshooting guide prepared

## Infrastructure Setup

### Database

- [ ] PostgreSQL instance created and tested
- [ ] Database user with appropriate permissions
- [ ] Backups configured and tested
- [ ] Connection pooling configured
- [ ] Database monitoring enabled
- [ ] Recovery procedure documented

### File Storage

- [ ] Storage location configured (disk or cloud)
- [ ] Backup strategy for uploaded files
- [ ] Cleanup policy for old files defined
- [ ] Storage permissions verified
- [ ] Monitoring for storage space

### Application Server

- [ ] Gunicorn configured with appropriate worker count
- [ ] Worker timeout tuned
- [ ] Max request size configured
- [ ] Graceful shutdown implemented
- [ ] Process monitoring setup (systemd, supervisor, etc.)

### Reverse Proxy (Nginx)

- [ ] SSL/TLS certificates installed
- [ ] HTTP → HTTPS redirect configured
- [ ] Headers configured (security, caching)
- [ ] Compression enabled (gzip)
- [ ] Load balancing configured if needed
- [ ] Rate limiting configured
- [ ] CORS headers set

### Monitoring & Logging

- [ ] Log aggregation setup (ELK, CloudWatch, etc.)
- [ ] Application metrics exposed (Prometheus)
- [ ] Alerting rules configured
- [ ] Health check monitoring setup
- [ ] Error rate monitoring
- [ ] Performance metrics collected
- [ ] Dashboard created

### Backup & Recovery

- [ ] Database backup schedule configured
- [ ] File storage backup configured
- [ ] Recovery tested and documented
- [ ] RTO/RPO defined and met
- [ ] Backup retention policy established

## Deployment Steps

### Build & Test

- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Docker image builds: `docker build -t dms:latest .`
- [ ] Docker image starts: `docker run -it dms:latest`

### Configuration

- [ ] .env file created with production settings
- [ ] DATABASE_URL configured for production database
- [ ] LOG_LEVEL set appropriately (INFO or WARNING)
- [ ] DEBUG set to False
- [ ] ALLOWED_FORMATS verified
- [ ] MAX_FILE_SIZE configured appropriately

### Database Initialization

- [ ] Database created: `createdb document_management`
- [ ] Tables created on first app startup (automatic)
- [ ] Database connection verified
- [ ] Test data loaded if needed

### Application Deployment

- [ ] Application deployed to server
- [ ] System service/container started
- [ ] Health check endpoint responds
- [ ] Logs are being written
- [ ] No startup errors
- [ ] Application restarted successfully

### Post-Deployment Testing

- [ ] Health check: `curl http://localhost:8000/health`
- [ ] Upload test: Upload a test file
- [ ] Retrieval test: Retrieve uploaded file
- [ ] Text extraction test: Verify extracted text
- [ ] Database test: Verify data in database
- [ ] Error handling: Test error scenarios
- [ ] Performance: Response times acceptable

### Monitoring Verification

- [ ] Logs being collected
- [ ] Metrics being collected
- [ ] Alerts working
- [ ] Dashboard showing data

## Runtime Operations

### Daily Checks

- [ ] Application is running
- [ ] No error spikes
- [ ] Response times normal
- [ ] Storage space adequate
- [ ] CPU/Memory usage normal

### Weekly Checks

- [ ] Backup success verified
- [ ] No unalert errors in logs
- [ ] Database performance good
- [ ] Disk space trend normal
- [ ] Network bandwidth normal

### Monthly Checks

- [ ] Full backup restore test
- [ ] Security logs reviewed
- [ ] Dependencies checked for updates
- [ ] Performance trends reviewed
- [ ] Capacity planning updated

## Scaling Checklist

### Horizontal Scaling

- [ ] Multiple application instances deployed
- [ ] Load balancer configured
- [ ] Session persistence configured if needed
- [ ] Database connection pool scaled
- [ ] Cache invalidation strategy defined

### Vertical Scaling

- [ ] Server resources increased
- [ ] Database resources increased
- [ ] Performance regression tested
- [ ] Cost impact analyzed

## Disaster Recovery

### Backup & Recovery

- [ ] Backup procedure automated
- [ ] Recovery procedure tested
- [ ] RTO verified: \_\_\_ minutes
- [ ] RPO verified: \_\_\_ minutes
- [ ] Runbooks prepared

### Incident Response

- [ ] On-call rotation established
- [ ] Escalation path defined
- [ ] Communication plan prepared
- [ ] Post-incident review process

## Security Audit

### Access Control

- [ ] API authentication implemented
- [ ] Rate limiting configured
- [ ] IP whitelisting if applicable
- [ ] API key rotation procedure defined

### Data Protection

- [ ] Data in transit encrypted (HTTPS)
- [ ] Data at rest encrypted if sensitive
- [ ] Backups encrypted
- [ ] Password policies enforced

### Compliance

- [ ] GDPR compliance verified if applicable
- [ ] Data retention policy enforced
- [ ] Audit logs maintained
- [ ] Security headers configured

## Documentation & Handoff

- [ ] Operations runbook completed
- [ ] Deployment procedure documented
- [ ] Scaling procedure documented
- [ ] Recovery procedure documented
- [ ] Troubleshooting guide completed
- [ ] Team trained on operations
- [ ] Contact information updated
- [ ] Escalation path documented

## Sign-Off

| Role            | Name | Date | Signature |
| --------------- | ---- | ---- | --------- |
| Developer       |      |      |           |
| Technical Lead  |      |      |           |
| DevOps          |      |      |           |
| Security        |      |      |           |
| Product Manager |      |      |           |

## Notes

Use this section for any additional notes or special considerations:

---

## Configuration Checklist (Copy to Prod)

```bash
# Production .env file
DATABASE_URL=postgresql://user:strong_password@prod-db:5432/document_management
DEBUG=False
LOG_LEVEL=INFO
UPLOAD_DIR=/data/uploads  # or cloud storage
MAX_FILE_SIZE=52428800  # 50 MB
ALLOWED_FORMATS=pdf,docx,png,txt
LOG_DIR=/var/log/dms
```

## Gunicorn Configuration

```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --worker-tmp-dir /dev/shm \
  --max-requests 10000 \
  --keep-alive 65 \
  --access-logfile /var/log/dms/access.log \
  --error-logfile /var/log/dms/error.log \
  --log-level info
```

## Nginx Configuration (Snippet)

```nginx
server {
    listen 443 ssl;
    server_name api.example.com;

    ssl_certificate /path/to/cert.crt;
    ssl_certificate_key /path/to/key.key;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Rate limiting
        limit_req zone=api burst=100 nodelay;

        # Timeouts
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}

# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
```

## Systemd Service (for Linux)

```ini
[Unit]
Description=Document Management Service
After=network.target

[Service]
Type=notify
User=dms
WorkingDirectory=/opt/dms
ExecStart=/opt/dms/venv/bin/gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

**Last Updated:** 2024-03-23
**Status:** Ready for deployment

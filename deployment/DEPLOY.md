# ContextFlow Deployment Guide

This guide covers deploying ContextFlow to production using Docker, Render, or Railway.

## Prerequisites

- Docker installed (for local deployment)
- Docker Compose installed (for local deployment)
- Account on Render or Railway (for cloud deployment)
- Git repository with your ContextFlow code

## Local Deployment with Docker

### Quick Start

```bash
# Build and start the services
docker-compose up -d

# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Using PostgreSQL (Production Mode)

1. Uncomment the `db` service in `docker-compose.yml`
2. Update `.env` with PostgreSQL credentials:
   ```bash
   DATABASE_URL=postgresql://contextflow:password@db:5432/contextflow
   ```
3. Restart the services:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Using Redis (Caching)

1. Uncomment the `redis` service in `docker-compose.yml`
2. Update `.env` with Redis URL:
   ```bash
   REDIS_URL=redis://redis:6379/0
   ```
3. Restart the services:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Deployment to Render

Render is a cloud platform that supports Docker deployments.

### Step 1: Prepare Your Repository

1. Ensure your code is pushed to GitHub
2. Create a `render.yaml` file in your repository root:
   ```yaml
   services:
     - type: web
       name: contextflow-api
       env: docker
       plan: free
       dockerfilePath: ./Dockerfile
       dockerContext: .
       autoDeploy: false
       envVars:
         - key: ENVIRONMENT
           value: production
         - key: PORT
           value: 8000
   ```

### Step 2: Deploy to Render

1. Go to [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Select the branch to deploy
5. Configure:
   - **Name**: contextflow-api
   - **Environment**: Docker
   - **Dockerfile Path**: ./Dockerfile
   - **Plan**: Free (or Starter for production)
6. Add environment variables from `.env.example`
7. Click "Create Web Service"

### Step 3: Verify Deployment

1. Wait for the deployment to complete
2. Check the deployment logs
3. Test the health endpoint:
   ```bash
   curl https://your-app-name.onrender.com/health
   ```

### Step 4: Connect a Database (Optional)

1. In Render dashboard, create a new PostgreSQL database
2. Add the internal database URL to your service environment variables:
   ```
   DATABASE_URL=postgresql://...
   ```
3. Redeploy your service

## Deployment to Railway

Railway is another cloud platform with excellent Docker support.

### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
```

### Step 2: Login to Railway

```bash
railway login
```

### Step 3: Initialize Project

```bash
railway init
```

### Step 4: Add Services

```bash
# Add API service
railway add --service contextflow-api

# Add PostgreSQL (optional)
railway add postgresql

# Add Redis (optional)
railway add redis
```

### Step 5: Configure Environment Variables

```bash
# Set environment variables
railway variables set ENVIRONMENT=production
railway variables set PORT=8000

# If using PostgreSQL
railway variables set DATABASE_URL=$DATABASE_URL

# If using Redis
railway variables set REDIS_URL=$REDIS_URL
```

### Step 6: Deploy

```bash
railway up
```

### Step 7: Get Public URL

```bash
railway domain
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `ENVIRONMENT` | Environment (development/production) | development |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | INFO |
| `DATABASE_URL` | Database connection string | sqlite:///./contextflow.db |
| `REDIS_URL` | Redis connection string (optional) | None |
| `SECRET_KEY` | Secret key for signing | Change in production |
| `CRITICAL_DRIFT_THRESHOLD` | Divergence threshold for RED consensus | 0.15 |
| `WARNING_DRIFT_THRESHOLD` | Divergence threshold for YELLOW consensus | 0.05 |

## Health Checks

The application includes a health check endpoint:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-08-12T10:00:00",
  "agents_tracked": 0,
  "journal_entries": 0
}
```

## Monitoring

### View Logs

**Docker Compose:**
```bash
docker-compose logs -f api
```

**Render:**
- Go to your service dashboard → Logs tab

**Railway:**
```bash
railway logs
```

### Metrics

Access metrics endpoint:
```bash
curl http://localhost:8000/metrics
```

## Troubleshooting

### Container Won't Start

1. Check logs: `docker-compose logs api`
2. Verify environment variables are set
3. Ensure ports are not already in use

### Database Connection Failed

1. Verify database service is running
2. Check DATABASE_URL format
3. Ensure network connectivity between services

### Health Check Failing

1. Verify the application is listening on the correct port
2. Check firewall settings
3. Ensure the health check endpoint is accessible

## Scaling

### Horizontal Scaling

**Docker Compose:**
```yaml
services:
  api:
    deploy:
      replicas: 3
```

**Render:**
- Upgrade to Starter plan
- Configure scaling in service settings

**Railway:**
- Automatic scaling based on plan

### Vertical Scaling

Increase resources in your deployment platform settings:
- CPU: 0.5 → 1 → 2 cores
- RAM: 512MB → 1GB → 2GB

## Security Best Practices

1. **Change Default Secrets**: Always change `SECRET_KEY` in production
2. **Use HTTPS**: Enable SSL/TLS in production
3. **Limit Access**: Use firewall rules to restrict access
4. **Regular Updates**: Keep dependencies updated
5. **Monitor Logs**: Regularly review logs for suspicious activity

## Backup and Recovery

### Database Backups

**PostgreSQL:**
```bash
# Backup
docker exec contextflow-db pg_dump -U contextflow contextflow > backup.sql

# Restore
docker exec -i contextflow-db psql -U contextflow contextflow < backup.sql
```

**SQLite:**
```bash
# Backup
cp contextflow.db contextflow.db.backup

# Restore
cp contextflow.db.backup contextflow.db
```

## Performance Optimization

1. **Enable Redis Caching**: Use Redis for SSV caching
2. **Use PostgreSQL**: Better performance than SQLite for production
3. **Increase Workers**: Set `WORKERS` environment variable based on CPU cores
4. **Enable Compression**: Use gzip compression for API responses

## Support

For issues or questions:
- Check the logs for error messages
- Review the troubleshooting section above
- Open an issue on GitHub

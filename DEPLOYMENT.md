# Deployment Guide - Moulya College Management System

This guide covers deployment options for the Moulya College Management System.

## Local Development Deployment

### Quick Start
1. Install Python 3.8+
2. Install dependencies: `pip install -r requirements.txt`
3. Initialize database: `python init_db.py`
4. Run application: `python app.py`
5. Access at `http://localhost:5000`

## Production Deployment

### Option 1: Traditional Server Deployment

#### Prerequisites
- Ubuntu/CentOS server
- Python 3.8+
- Nginx (recommended)
- Gunicorn (WSGI server)

#### Steps

1. **Server Setup**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and pip
   sudo apt install python3 python3-pip python3-venv -y
   
   # Install Nginx
   sudo apt install nginx -y
   ```

2. **Application Setup**
   ```bash
   # Create application directory
   sudo mkdir -p /var/www/moulya
   cd /var/www/moulya
   
   # Copy application files
   # (Upload your project files here)
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   pip install gunicorn
   
   # Initialize database
   python init_db.py
   
   # Create sample data (optional)
   python sample_data.py
   ```

3. **Gunicorn Configuration**
   ```bash
   # Create gunicorn config
   sudo nano /var/www/moulya/gunicorn.conf.py
   ```
   
   Add the following content:
   ```python
   bind = "127.0.0.1:8000"
   workers = 3
   worker_class = "sync"
   worker_connections = 1000
   timeout = 30
   keepalive = 2
   max_requests = 1000
   max_requests_jitter = 100
   preload_app = True
   ```

4. **Systemd Service**
   ```bash
   sudo nano /etc/systemd/system/moulya.service
   ```
   
   Add the following content:
   ```ini
   [Unit]
   Description=Moulya College Management System
   After=network.target
   
   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/var/www/moulya
   Environment="PATH=/var/www/moulya/venv/bin"
   ExecStart=/var/www/moulya/venv/bin/gunicorn -c gunicorn.conf.py app:app
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

5. **Nginx Configuration**
   ```bash
   sudo nano /etc/nginx/sites-available/moulya
   ```
   
   Add the following content:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;  # Replace with your domain
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
       
       location /static {
           alias /var/www/moulya/static;
           expires 1y;
           add_header Cache-Control "public, immutable";
       }
   }
   ```

6. **Enable and Start Services**
   ```bash
   # Enable Nginx site
   sudo ln -s /etc/nginx/sites-available/moulya /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   
   # Enable and start Moulya service
   sudo systemctl enable moulya
   sudo systemctl start moulya
   
   # Check status
   sudo systemctl status moulya
   ```

### Option 2: Docker Deployment

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   RUN python init_db.py
   
   EXPOSE 5000
   
   CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
   ```

2. **Create docker-compose.yml**
   ```yaml
   version: '3.8'
   
   services:
     moulya:
       build: .
       ports:
         - "5000:5000"
       volumes:
         - ./data:/app/data
       environment:
         - FLASK_ENV=production
       restart: unless-stopped
   ```

3. **Deploy**
   ```bash
   docker-compose up -d
   ```

### Option 3: Cloud Platform Deployment

#### Heroku Deployment

1. **Create Procfile**
   ```
   web: gunicorn app:app
   ```

2. **Create runtime.txt**
   ```
   python-3.9.18
   ```

3. **Deploy**
   ```bash
   # Install Heroku CLI
   # Create Heroku app
   heroku create moulya-college
   
   # Deploy
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

## Environment Configuration

### Production Settings

Create a `.env` file for production:
```env
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=sqlite:///production.db
```

Update `config.py` to use environment variables:
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fallback-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///moulya_college.db'
    # ... other settings
```

## Security Considerations

### Production Security Checklist

- [ ] Change default admin password
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS (SSL/TLS)
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Database backups
- [ ] Monitor logs
- [ ] Limit file upload sizes
- [ ] Validate all user inputs

### SSL/HTTPS Setup

1. **Using Let's Encrypt (Certbot)**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

2. **Update Nginx configuration** (automatic with certbot)

## Database Management

### Backup
```bash
# SQLite backup
cp /var/www/moulya/moulya_college.db /backup/location/
```

### Restore
```bash
# SQLite restore
cp /backup/location/moulya_college.db /var/www/moulya/
```

## Monitoring and Maintenance

### Log Files
- Application logs: Check systemd journal with `sudo journalctl -u moulya`
- Nginx logs: `/var/log/nginx/access.log` and `/var/log/nginx/error.log`

### Health Checks
```bash
# Check service status
sudo systemctl status moulya
sudo systemctl status nginx

# Check application response
curl -I http://localhost:8000
```

### Updates
```bash
# Update application
cd /var/www/moulya
git pull origin main  # if using git
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart moulya
```

## Performance Optimization

### Database Optimization
- Regular VACUUM for SQLite
- Index optimization
- Query optimization

### Caching
- Static file caching via Nginx
- Application-level caching if needed

### Scaling
- Increase Gunicorn workers
- Load balancing with multiple servers
- Database replication for read scaling

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo journalctl -u moulya -f
   ```

2. **Database permission issues**
   ```bash
   sudo chown -R www-data:www-data /var/www/moulya
   ```

3. **Nginx configuration errors**
   ```bash
   sudo nginx -t
   ```

### Recovery Procedures

1. **Service recovery**
   ```bash
   sudo systemctl restart moulya
   sudo systemctl restart nginx
   ```

2. **Database recovery**
   ```bash
   # Restore from backup
   cp /backup/moulya_college.db /var/www/moulya/
   sudo chown www-data:www-data /var/www/moulya/moulya_college.db
   ```

## Support and Maintenance

### Regular Maintenance Tasks
- Weekly: Check logs and system status
- Monthly: Update system packages
- Quarterly: Review security settings
- Annually: Update SSL certificates (if not auto-renewed)

### Monitoring Setup
Consider setting up monitoring tools like:
- Uptime monitoring
- Log aggregation
- Performance monitoring
- Security scanning
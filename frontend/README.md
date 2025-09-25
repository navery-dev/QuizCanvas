# QuizCanvas - Customizable Learning Platform

QuizCanvas is a web-based quiz application that allows users to create, manage, and take customizable quizzes for learning and certification preparation. Built with modern web technologies, it provides a comprehensive solution for educational content delivery and progress tracking.

## Features

### Core Functionality
- **Custom Quiz Creation**: Upload quiz content via CSV or JSON files
- **Interactive Quiz Taking**: Navigate between questions, set timers, and track progress
- **Progress Analytics**: Detailed performance tracking and improvement metrics
- **User Management**: Secure registration, authentication, and profile management
- **File Management**: Cloud-based storage for quiz files and user data

### Security Features
- **JWT Authentication**: Secure token-based user sessions
- **Password Reset**: Email-based secure password recovery with time-limited tokens
- **SSL/HTTPS**: End-to-end encryption for all communications
- **Input Validation**: Protection against malicious file uploads and data injection

### Technical Architecture
- **Frontend**: React.js application hosted on GitHub Pages
- **Backend**: Django REST API on AWS EC2 with Nginx reverse proxy
- **Database**: PostgreSQL hosted on Neon.tech
- **File Storage**: AWS S3 for quiz content and media files
- **CI/CD**: GitHub Actions for automated deployment

## Live Application

- **Frontend**: https://quizcanvas.xyz
- **API**: https://api.quizcanvas.xyz
- **Admin Interface**: https://api.quizcanvas.xyz/admin/

## Backend Infrastructure Setup Guide

This guide will walk you through recreating the complete backend infrastructure on AWS EC2 from scratch.

### Prerequisites

- AWS Account with EC2 and S3 access
- Domain name (optional but recommended for SSL)
- Neon.tech account for PostgreSQL database
- Outlook/Office 365 account for email services

### Step 1: AWS EC2 Instance Setup

1. **Launch EC2 Instance**
   ```bash
   # Instance Configuration:
   # - AMI: Amazon Linux 2023
   # - Instance Type: t2.micro (free tier eligible)
   # - Key Pair: Create new key pair and download .pem file
   ```

2. **Configure Security Group**
   ```bash
   # Inbound Rules:
   # SSH (22) - Your IP only
   # HTTP (80) - 0.0.0.0/0
   # HTTPS (443) - 0.0.0.0/0
   ```

3. **Connect to Instance**
   ```bash
   ssh -i your-key.pem ec2-user@your-ec2-ip
   ```

### Step 2: System Configuration

1. **Update System and Install Dependencies**
   ```bash
   # Update system packages
   sudo yum update -y
   
   # Install Python, pip, git, and nginx
   sudo yum install -y python3 python3-pip git nginx
   
   # Install certbot for SSL certificates
   sudo yum install -y python3-certbot-nginx
   ```

2. **Create Application Directory**
   ```bash
   # Create directory structure
   sudo mkdir -p /var/www/quizcanvas
   sudo chown ec2-user:ec2-user /var/www/quizcanvas
   cd /var/www/quizcanvas
   ```

### Step 3: Application Deployment

1. **Clone Repository**
   ```bash
   # Clone your repository
   git clone https://github.com/your-username/QuizCanvas.git .
   cd backend
   ```

2. **Python Environment Setup**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install Python dependencies
   pip install -r requirements.txt
   pip install gunicorn
   ```

3. **Environment Configuration**
   ```bash
   # Create .env file
   nano .env
   ```
   
   Add the following environment variables:
   ```env
   SECRET_KEY=your-django-secret-key-here
   DATABASE_URL=postgres://user:password@host:port/database_name
   AWS_ACCESS_KEY_ID=your-aws-access-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret-key
   AWS_S3_ARN=arn:aws:s3:::your-bucket-name
   AWS_STORAGE_BUCKET_NAME=your-bucket-name
   ALLOWED_HOSTS=api.yourdomain.com,127.0.0.1,localhost
   DEBUG=False
   EMAIL_HOST=smtp.office365.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your-outlook-email@outlook.com
   EMAIL_HOST_PASSWORD=your-outlook-app-password
   EMAIL_USE_TLS=True
   DEFAULT_FROM_EMAIL="QuizCanvas <your-outlook-email@outlook.com>"
   FRONTEND_BASE_URL=https://yourdomain.com
   ```

4. **Database Migration**
   ```bash
   # Run database migrations
   python manage.py migrate
   
   # Collect static files
   python manage.py collectstatic --noinput
   
   # Create superuser (optional)
   python manage.py createsuperuser
   ```

### Step 4: Gunicorn Service Configuration

1. **Create Gunicorn Service File**
   ```bash
   sudo nano /etc/systemd/system/gunicorn.service
   ```
   
   Add the following content:
   ```ini
   [Unit]
   Description=Gunicorn instance to serve QuizCanvas
   After=network.target
   
   [Service]
   User=ec2-user
   Group=nginx
   WorkingDirectory=/var/www/quizcanvas/backend
   Environment="PATH=/var/www/quizcanvas/backend/venv/bin"
   EnvironmentFile=/var/www/quizcanvas/backend/.env
   ExecStart=/var/www/quizcanvas/backend/venv/bin/gunicorn --workers 3 --bind unix:/var/www/quizcanvas/backend/gunicorn.sock config.wsgi:application
   ExecReload=/bin/kill -s HUP $MAINPID
   Restart=on-failure
   
   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable and Start Gunicorn**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable gunicorn
   sudo systemctl start gunicorn
   sudo systemctl status gunicorn
   ```

### Step 5: Nginx Configuration

1. **Create Nginx Configuration**
   ```bash
   sudo nano /etc/nginx/nginx.conf
   ```
   
   Replace the contents with:
   ```nginx
   user nginx;
   worker_processes auto;
   error_log /var/log/nginx/error.log notice;
   pid /run/nginx.pid;
   
   include /usr/share/nginx/modules/*.conf;
   
   events {
       worker_connections 1024;
   }
   
   http {
       log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                       '$status $body_bytes_sent "$http_referer" '
                       '"$http_user_agent" "$http_x_forwarded_for"';
   
       access_log /var/log/nginx/access.log main;
   
       sendfile on;
       tcp_nopush on;
       keepalive_timeout 65;
       types_hash_max_size 4096;
   
       include /etc/nginx/mime.types;
       default_type application/octet-stream;
       include /etc/nginx/conf.d/*.conf;
   
       server {
           listen 80 default_server;
           listen [::]:80 default_server;
           server_name _;
           root /var/www/html;
   
           include /etc/nginx/default.d/*.conf;
   
           error_page 404 /404.html;
           error_page 500 502 503 504 /50x.html;
   
           location / {
               return 200 "Server is running";
               add_header Content-Type text/plain;
           }
       }
   
       # API server block
       server {
           listen 80;
           listen [::]:80;
           server_name api.yourdomain.com;  # Replace with your domain
           root /var/www/html;
   
           include /etc/nginx/default.d/*.conf;
   
           error_page 404 /404.html;
           error_page 500 502 503 504 /50x.html;
   
           location / {
               proxy_pass http://unix:/var/www/quizcanvas/backend/gunicorn.sock;
               proxy_set_header Host $host;
               proxy_set_header X-Real-IP $remote_addr;
               proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
               proxy_set_header X-Forwarded-Proto $scheme;
               proxy_set_header X-Forwarded-Host $host;
               proxy_redirect off;
           }
       }
   }
   ```

2. **Test and Start Nginx**
   ```bash
   sudo nginx -t
   sudo systemctl enable nginx
   sudo systemctl start nginx
   sudo systemctl status nginx
   ```

### Step 6: SSL Certificate Setup

1. **Install SSL Certificate**
   ```bash
   # Replace api.yourdomain.com with your actual domain
   sudo certbot --nginx -d api.yourdomain.com
   ```

2. **Set Up Auto-Renewal**
   ```bash
   # Create renewal service
   sudo tee /etc/systemd/system/certbot-renewal.service > /dev/null << 'EOF'
   [Unit]
   Description=Certbot Renewal
   After=syslog.target
   
   [Service]
   Type=oneshot
   ExecStart=/usr/bin/certbot renew --quiet --no-self-upgrade --deploy-hook "systemctl reload nginx"
   User=root
   EOF
   
   # Create renewal timer
   sudo tee /etc/systemd/system/certbot-renewal.timer > /dev/null << 'EOF'
   [Unit]
   Description=Run certbot twice daily
   Requires=certbot-renewal.service
   
   [Timer]
   OnCalendar=*-*-* 00,12:00:00
   RandomizedDelaySec=3600
   Persistent=true
   
   [Install]
   WantedBy=timers.target
   EOF
   
   # Enable and start timer
   sudo systemctl daemon-reload
   sudo systemctl enable certbot-renewal.timer
   sudo systemctl start certbot-renewal.timer
   ```

### Step 7: External Services Setup

1. **AWS S3 Bucket**
   - Create S3 bucket in AWS Console
   - Configure bucket permissions for read/write access
   - Generate IAM user with S3 access permissions
   - Note bucket name and ARN for environment variables

2. **Neon PostgreSQL Database**
   - Create account at [Neon.tech](https://neon.tech/)
   - Create new database project
   - Copy connection string for DATABASE_URL environment variable

3. **Email Configuration**
   - Use Outlook/Office 365 account
   - Generate app-specific password (not regular password)
   - Configure SMTP settings in environment variables

### Step 8: Verification and Testing

1. **Test API Endpoints**
   ```bash
   # Test health endpoint
   curl https://api.yourdomain.com/api/health/
   
   # Test admin interface
   curl -I https://api.yourdomain.com/admin/
   ```

2. **Check Service Status**
   ```bash
   sudo systemctl status gunicorn
   sudo systemctl status nginx
   sudo systemctl status certbot-renewal.timer
   ```

3. **Monitor Logs**
   ```bash
   # Gunicorn logs
   sudo journalctl -u gunicorn -f
   
   # Nginx logs
   sudo tail -f /var/log/nginx/access.log
   sudo tail -f /var/log/nginx/error.log
   ```

### Step 9: CI/CD Setup (Optional)

For automated deployments, set up GitHub Actions with a self-hosted runner on your EC2 instance.

1. **Install GitHub Runner**
   ```bash
   # Follow GitHub's instructions for self-hosted runners
   # https://github.com/your-repo/settings/actions/runners/new
   ```

2. **Configure Deployment Secrets**
   In your GitHub repository settings, add these secrets:
   - `SECRET_KEY`
   - `DATABASE_URL`
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_S3_ARN`
   - `AWS_STORAGE_BUCKET_NAME`
   - `EMAIL_HOST_USER`
   - `EMAIL_HOST_PASSWORD`

## Troubleshooting

### Common Issues

1. **Gunicorn Socket Permission Errors**
   ```bash
   sudo chown ec2-user:nginx /var/www/quizcanvas/backend/gunicorn.sock
   ```

2. **SSL Certificate Issues**
   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

3. **Database Connection Problems**
   ```bash
   cd /var/www/quizcanvas/backend
   source venv/bin/activate
   python manage.py dbshell
   ```

4. **Static Files Not Loading**
   ```bash
   python manage.py collectstatic --noinput
   sudo systemctl restart nginx
   ```

## Contributing

This project is part of a semester-long software development course. The application demonstrates professional-level development practices including:

- Object-oriented design and development
- Database design and implementation
- RESTful API development
- Frontend-backend integration
- Cloud deployment and DevOps practices
- Security implementation and SSL/HTTPS
- Automated testing and deployment pipelines

## License

This project is developed for educational purposes as part of Columbia Basin College's software development curriculum.
# QuizCanvas

Web-based learning platform for creating customizable multiple-choice quizzes

## Project Overview
QuizCanvas is designed to provide a flexible, user-friendly platform for quiz-based learning. QuizCanvas allows users to upload their own content via CSV or JSON files, making it universally applicable across any subject domain.

## Context
Course: CS421 Software Development Capstone Project  
Status: Production Ready

## Feature Roadmap
- Tune Mastery Level calculations
- Update User Profile statistics
- Add password reset functionality
- Add individual question and section statistics

## Development Setup

### Architecture

- **Frontend:** React.js hosted on GitHub Pages
- **Backend:** Django with Gunicorn/Nginx on AWS EC2
- **Database:** PostgreSQL on Neon.tech
- **File Storage:** AWS S3
- **CI/CD:** GitHub Actions

### Running Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/navery-dev/QuizCanvas.git
   cd QuizCanvas
   ```

2. **Backend Setup:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Create local environment file
   cp .env.example .env  # Create this file with local settings
   # Edit .env with your local database and AWS credentials
   
   # Setup database
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser  # Optional: for admin access
   ```

3. **Frontend Setup:**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Start Development Servers:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   source venv/bin/activate
   python manage.py runserver
   
   # Terminal 2 - Frontend  
   cd frontend
   npm start
   ```

## Production Deployment

### AWS EC2 Setup

1. **Initial Server Setup:**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install required packages
   sudo apt install python3 python3-pip python3-venv nginx git -y
   
   # Create application user
   sudo useradd -m -s /bin/bash quizcanvas
   sudo mkdir -p /var/www/quizcanvas
   sudo chown quizcanvas:quizcanvas /var/www/quizcanvas
   ```

2. **Deploy Application:**
   ```bash
   # Switch to app user
   sudo su - quizcanvas
   cd /var/www/quizcanvas
   
   # Clone repository
   git clone https://github.com/navery-dev/QuizCanvas.git .
   
   # Setup backend
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Environment variables will be created by GitHub Actions
   # But for manual setup, create .env file with production values
   ```

3. **Configure Gunicorn Service:**
   ```bash
   sudo nano /etc/systemd/system/gunicorn.service
   ```
   
   Add the following content:
   ```ini
   [Unit]
   Description=Gunicorn instance to serve QuizCanvas
   After=network.target
   
   [Service]
   User=quizcanvas
   Group=quizcanvas
   WorkingDirectory=/var/www/quizcanvas/backend
   Environment="PATH=/var/www/quizcanvas/backend/venv/bin"
   ExecStart=/var/www/quizcanvas/backend/venv/bin/gunicorn --workers 3 --bind unix:/var/www/quizcanvas/backend/quizcanvas.sock config.wsgi:application
   ExecReload=/bin/kill -s HUP $MAINPID
   Restart=on-failure
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **Configure Nginx:**
   ```bash
   sudo nano /etc/nginx/sites-available/quizcanvas
   ```
   
   Add the following content:
   ```nginx
   server {
       listen 80;
       server_name api.quizcanvas.xyz;
       
       location / {
           include proxy_params;
           proxy_pass http://unix:/var/www/quizcanvas/backend/quizcanvas.sock;
       }
       
       location /static/ {
           alias /var/www/quizcanvas/backend/static/;
       }
   }
   ```

5. **Enable Services:**
   ```bash
   # Enable nginx site
   sudo ln -s /etc/nginx/sites-available/quizcanvas /etc/nginx/sites-enabled/
   sudo nginx -t
   
   # Start and enable services
   sudo systemctl daemon-reload
   sudo systemctl enable gunicorn
   sudo systemctl start gunicorn
   sudo systemctl restart nginx
   
   # Check status
   sudo systemctl status gunicorn
   sudo systemctl status nginx
   ```

### Environment Variables

Create a `.env` file in `backend/` containing:
```bash
SECRET_KEY=your-django-secret-key-here
DATABASE_URL=postgres://user:password@host:port/database_name
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_S3_ARN=arn:aws:s3:::your-bucket-name
AWS_STORAGE_BUCKET_NAME=your-bucket-name
ALLOWED_HOSTS=[addCustomHostName],127.0.0.1,localhost
DEBUG=False
```

### External Services Setup

#### AWS S3 Setup
1. Create an S3 bucket in AWS Console
2. Set bucket permissions for read/write access
3. Generate IAM credentials with S3 access
4. Note the bucket name and ARN

#### Neon PostgreSQL Setup
1. Create account at [Neon.tech](https://neon.tech/)
2. Create a new database
3. Copy the connection string
4. Set as `DATABASE_URL` in environment variables

### GitHub Secrets Configuration

Configure these secrets in your GitHub repository settings:

**Required Secrets:**
- `SECRET_KEY` - Django secret key
- `DATABASE_URL` - Neon PostgreSQL connection string  
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_S3_ARN` - S3 bucket ARN
- `AWS_STORAGE_BUCKET_NAME` - S3 bucket name
- `REACT_APP_API_URL` - Backend API URL (Custom Host Name)

**Auto-provided Secrets:**
- `GITHUB_TOKEN` - Automatically provided by GitHub

### CI/CD Workflows

The repository includes two GitHub Actions workflows:

#### Backend Deployment (`backend-deploy.yml`)
- Triggers on changes to `backend/` or workflow file
- Uses self-hosted runner on EC2 instance
- Installs dependencies, runs migrations, collects static files
- Restarts Gunicorn and Nginx services

#### Frontend Deployment (`frontend-deploy.yml`)
- Triggers on changes to `frontend/` or workflow file
- Builds React application with production API URL
- Creates 404.html for SPA routing support
- Deploys to GitHub Pages

### Manual Deployment Commands

If deploying manually on EC2:

```bash
# Navigate to project directory
cd /var/www/quizcanvas/backend

# Activate virtual environment
source venv/bin/activate

# Update code
git pull origin main

# Install dependencies
pip install -r requirements.txt

# Run Django commands
python manage.py migrate
python manage.py collectstatic --noinput

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# Verify deployment
curl -f http://localhost/ || echo "Application not responding"
```

## Troubleshooting

### Common Issues

1. **Gunicorn won't start:**
   ```bash
   # Check logs
   sudo journalctl -u gunicorn -f
   
   # Verify socket file permissions
   ls -la /var/www/quizcanvas/backend/quizcanvas.sock
   ```

2. **Nginx 502 Bad Gateway:**
   ```bash
   # Check if Gunicorn is running
   sudo systemctl status gunicorn
   
   # Check Nginx configuration
   sudo nginx -t
   ```

3. **Database connection issues:**
   ```bash
   # Test database connection
   cd backend
   python manage.py dbshell
   ```

4. **Static files not loading:**
   ```bash
   # Ensure static files are collected
   python manage.py collectstatic --noinput
   
   # Check permissions
   ls -la /var/www/quizcanvas/backend/static/
   ```
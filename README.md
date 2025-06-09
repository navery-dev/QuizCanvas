# QuizCanvas

Web-based learning platform for creating customizable multiple-choice quizzes

## Project Overview
QuizCanvas is designed to provide a flexible, user-friendly platform for quiz-based learning. QuizCanvas allows users to upload their own content via CSV or JSON files, making it universally applicable across any subject domain.

## Context
Course: CS421 Software Development Capstone Project
Status: Basic function complete

## Feature Roadmap
- Tune Mastery Level calculations
- Update User Profile statistics
- Add password reset functionality
- Add individual question and section statistics

## Usage and Deployment

### Running Locally
1. Clone the repository and install dependencies:
   ```bash
   git clone https://github.com/[yourOrg]/[yourRepository].git
   cd [yourRepository]
   pip install -r backend/requirements.txt
   npm --prefix frontend install
   ```
2. Start the backend and frontend:
   ```bash
   python backend/manage.py runserver
   npm --prefix frontend start
   ```

### Required Packages on EC2
Install Python 3, `virtualenv`, `git`, `nginx`, and `gunicorn` on the EC2 instance.

### Environment Variables
Create a `.env` in `backend/` containing:
```
SECRET_KEY=your-django-secret
DATABASE_URL=postgres://<user>:<password>@<host>/<db_name>  # Neon connection
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
AWS_S3_ARN=arn:aws:s3:::<bucket-name>
AWS_STORAGE_BUCKET_NAME=<bucket-name>
ALLOWED_HOSTS=your.domain,127.0.0.1,localhost
```

### AWS S3 Setup
1. Create an S3 bucket.
2. Note the bucket name and ARN and grant read/write permissions.
3. Store the access keys in the `.env` file and as GitHub secrets.

### Neon Postgres
1. Create a database on [Neon](https://neon.tech/).
2. Copy the connection string and set it as `DATABASE_URL` locally, on EC2, and in GitHub secrets.

### GitHub Secrets
The GitHub Actions workflows require these secrets:
`SECRET_KEY`, `DATABASE_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_ARN`, `AWS_STORAGE_BUCKET_NAME`, and `REACT_APP_API_URL`.

### GitHub Actions Workflows
- **backend-deploy.yml**: deploys the Django backend to the EC2 instance. It installs dependencies, writes the `.env`, runs migrations, collects static files, and restarts `gunicorn` and `nginx`.
- **frontend-deploy.yml**: builds the React app with `REACT_APP_API_URL` and publishes to GitHub Pages.

### EC2 Deployment Steps
1. SSH to the EC2 instance.
2. Activate the virtual environment and install dependencies: `pip install -r backend/requirements.txt`.
3. Run `python manage.py migrate` and `python manage.py collectstatic`.
4. Restart `gunicorn` and `nginx` to apply changes.

The frontend is served from GitHub Pages and communicates with the API using the `REACT_APP_API_URL` value.
# Student Management System - Automated CI/CD Pipeline

A small Flask REST API for managing student records, used to demonstrate an
automated CI/CD pipeline with GitHub Actions and Docker.

## Pipeline

```
Push / Pull Request
        |
        v
 [CI] Lint (flake8) + Unit tests (pytest, 80% coverage gate)
        |
        v
 [Build] Docker image -> GitHub Container Registry (sha + latest tags)
        |
        v
 [Smoke test] Run container, curl /health
        |
        v
 [CD] SSH to server, pull new image, restart container
```

- Every push and pull request runs lint and tests.
- Pushes to `main` build and push the image to GHCR, smoke test it, then deploy.
- Deployment is skipped automatically if server secrets are not configured.

## Project structure

```
student-management-system/
├── app.py                      # Flask app + SQLite data layer
├── tests/test_app.py           # pytest test suite
├── requirements.txt            # Runtime dependencies
├── requirements-dev.txt        # Test/lint dependencies
├── Dockerfile                  # Production image (gunicorn)
├── docker-compose.yml          # Local container run
└── .github/workflows/ci-cd.yml # CI/CD pipeline definition
```

## Run locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
python app.py
```

The API is available at `http://localhost:5000`.

## Run tests

```bash
flake8 .
pytest --cov=app --cov-report=term-missing
```

## Run with Docker

```bash
docker compose up --build
curl http://localhost:5000/health
```

## API endpoints

| Method | Endpoint            | Description            |
|--------|---------------------|------------------------|
| GET    | `/health`           | Health check           |
| GET    | `/students`         | List all students      |
| GET    | `/students/<id>`    | Get one student        |
| POST   | `/students`         | Create a student       |
| PUT    | `/students/<id>`    | Update a student       |
| DELETE | `/students/<id>`    | Delete a student       |

Example request:

```bash
curl -X POST http://localhost:5000/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice Kumar","email":"alice@college.edu","course":"CSE","year":2}'
```

## Required GitHub secrets for deployment

| Secret          | Purpose                          |
|-----------------|----------------------------------|
| `DEPLOY_HOST`   | Server IP or hostname            |
| `DEPLOY_USER`   | SSH username                     |
| `DEPLOY_SSH_KEY`| Private SSH key for the server   |

`GITHUB_TOKEN` is provided automatically and is used to push/pull the image.
If the deploy secrets are absent, the deploy job prints a notice and is skipped.

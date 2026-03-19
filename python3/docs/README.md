# Python Production Guide

A documentation set teaching experienced JavaScript engineers how to build and deploy Python web applications.

## What This Is

This guide walks you through building a production-ready FastAPI service from scratch, covering the full journey from project setup to deployment on multiple platforms.

## Target Audience

Senior JavaScript/Node developers who can read and write Python but lack confidence in Python packaging, runtime models, and deployment conventions.

## Tech Stack

- **Framework:** FastAPI
- **Dependency Management:** uv
- **Testing:** pytest
- **Linting/Formatting:** Ruff
- **Database:** PostgreSQL with SQLAlchemy and Alembic
- **Containerization:** Docker and Docker Compose

## Reading Order

### Core Application Path

1. [Overview](00-overview.md) - What this guide covers and why
2. [Python vs Node Appendix](appendix-python-vs-node.md) - Mental model mapping for JS developers
3. [Project Setup](01-project-setup.md) - Bootstrap a Python project with uv
4. [Build the API](02-build-the-api.md) - Create a FastAPI application
5. [Testing and Quality](03-testing-quality.md) - pytest, Ruff, and type hints
6. [Data and Migrations](04-data-and-migrations.md) - PostgreSQL, SQLAlchemy, Alembic
7. [Production Concerns](05-production-concerns.md) - Config, logging, health checks, workers
8. [Containerization](06-containerization.md) - Docker and Docker Compose
9. [CI/CD](07-ci-cd.md) - GitHub Actions pipeline

### Deployment Guides

10. [Deploy to VPS](deploy-vps.md) - Self-managed Linux server with Docker Compose
11. [Deploy to AWS Fargate](deploy-aws-fargate.md) - Managed container infrastructure
12. [Deploy to Fly.io](deploy-flyio.md) - Simplified managed deployment

## Quick Start

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize project
uv init
uv venv
uv add fastapi uvicorn pydantic-settings
uv add --dev pytest ruff

# Run the app
uv run uvicorn app.main:app --reload
```

## Quick Reference

See [../CHEATSHEET.md](../CHEATSHEET.md) for a condensed reference covering:

- Project structure
- Type hints
- Pydantic models
- FastAPI patterns
- SQLAlchemy queries
- Testing patterns
- Async/await
- Common gotchas
- Performance tips

## License

This documentation is provided for learning purposes.

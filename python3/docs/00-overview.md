# Python Production Overview

## Who This Guide Is For

This guide is for an experienced JavaScript engineer who already understands web backends, APIs, containers, and deployment at a high level, but does not yet have strong Python production instincts. You do not need help learning `if`, `for`, or classes. You need help learning the ecosystem conventions that turn Python code into a service you can actually run, test, ship, and maintain.

## What You Will Build

You will build one small but realistic `FastAPI` service. The app will expose HTTP endpoints, connect to PostgreSQL, use migrations, run tests, enforce code quality, read configuration from environment variables, and run in Docker.

Then you will deploy the same application shape in three different ways:

- a Linux VPS using Docker Compose
- AWS ECS/Fargate using managed container infrastructure
- Fly.io as a simpler managed deployment comparison

## What Production-Ready Means in Python

In this guide, production-ready does not mean perfect. It means the service is packaged predictably, configured by environment, tested automatically, observable enough to operate, and deployable without manual file copying.

For a Python web app, that usually includes:

- isolated dependencies and a lockfile
- a clear `pyproject.toml`
- a real application server process model
- database migrations
- health checks
- logging
- container images
- CI checks for linting and tests
- environment-based secrets and config

## What This Guide Covers

The learning path is split into a shared application track and deployment-specific tracks.

The shared track covers:

- project bootstrapping with `uv`
- application structure with `FastAPI`
- testing with `pytest`
- formatting and linting with `ruff`
- data access with `SQLAlchemy`
- schema migrations with `Alembic`
- production concerns such as env vars, health checks, and workers
- containerization with Docker
- CI/CD fundamentals

The deployment tracks then show how the same app fits into:

- a self-managed VPS
- AWS ECS/Fargate
- Fly.io

## What This Guide Does Not Cover

This guide intentionally avoids trying to teach all of Python infrastructure at once.

It does not focus on:

- Kubernetes
- serverless Lambda-style deployment
- advanced distributed systems patterns
- deep cloud security architecture
- Python packaging for desktop apps or libraries
- code obfuscation as a normal backend release step

## Why Python Backend Deployment Is Different From JS Bundling

If you come from JavaScript, especially frontend or full-stack Node work, you may expect a production build step to center on bundling, minification, tree-shaking, and obfuscation.

That is not the normal backend Python story.

For Python services, production preparation usually focuses on:

- locking dependencies
- building a container image
- selecting the process model
- setting environment variables
- running migrations
- wiring logs, health checks, and secrets

The Python application code itself is usually shipped as source inside the image. Python may generate `.pyc` bytecode files at runtime or install time, but that is not the same thing as a JavaScript production bundling pipeline.

If your Python service also serves frontend assets, then those frontend assets still go through their normal JavaScript or CSS build process. The difference is that this build step belongs to the frontend layer, not the Python backend runtime model.

## Recommended Reading Order

Read the docs in this order:

1. `docs/00-overview.md`
2. `docs/appendix-python-vs-node.md`
3. `docs/01-project-setup.md`
4. `docs/02-build-the-api.md`
5. `docs/03-testing-quality.md`
6. `docs/04-data-and-migrations.md`
7. `docs/05-production-concerns.md`
8. `docs/06-containerization.md`
9. `docs/07-ci-cd.md`
10. `docs/deploy-vps.md`
11. `docs/deploy-aws-fargate.md`
12. `docs/deploy-flyio.md`

If you want the broadest learning payoff, start with the VPS guide after the shared path, then read the AWS and Fly.io guides as comparisons.

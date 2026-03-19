# CI/CD

Once the app has tests and a container image, you want machines to validate and ship it consistently. CI/CD is what turns your quality expectations into something repeatable instead of something you remember to do on good days.

## Continuous Integration

Continuous Integration is the part that proves changes are safe enough to merge.

For the service in this guide, CI should usually run at least:

- formatting checks or formatting enforcement rules
- linting
- tests
- optionally container image build validation

A minimal mental model is: every branch should prove the app still installs, still passes quality checks, and still behaves as expected.

Typical CI commands for this repo shape:

```bash
uv run ruff check .
uv run pytest
docker build -t python-production-guide .
```

You may also choose to run `uv run ruff format --check .` or an equivalent formatting validation strategy depending on how strict you want CI to be.

## Continuous Delivery

Continuous Delivery is about making the app deployable at any time, even if actual production release still requires an explicit approval step.

For this guide, that usually means CI also produces or validates:

- a buildable Docker image
- a tagged image for the container registry
- deployment metadata tied to a commit or release

Delivery becomes easier once the app artifact is clear. In this case, the main artifact is the container image.

## Example Pipeline Stages

A pragmatic pipeline can be thought of in stages:

1. checkout code
2. install dependencies
3. run linting and tests
4. build container image
5. push image to registry for deployable branches or tags
6. run deployment workflow for the target environment

This is intentionally simple. You can add caching, preview environments, and release automation later.

## Deployment Promotion Strategy

Do not think of deployment as just "run one command in prod." Think in terms of promotion between levels of confidence.

A common progression is:

- feature branch: run linting and tests
- main branch: build and publish a trusted image
- staging: deploy and verify environment behavior
- production: promote a known image, run migrations carefully, monitor rollout

The key idea is that the image you deploy should already have passed quality checks. Deployment should not be the first time you discover syntax issues, import errors, or failing tests.

## Example GitHub Actions Workflow

If you use GitHub Actions, here is a complete workflow that runs tests, builds the image, and pushes to a container registry on the `main` branch:

```yaml
name: ci

on:
  push:
    branches: [main]
  pull_request:

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - run: uv sync

      - run: uv run ruff format --check .

      - run: uv run ruff check .

      - run: uv run pytest

  build-and-push:
    runs-on: ubuntu-latest
    needs: test
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/build-push-action@v6
        with:
          context: .
          push: ${{ github.event_name == 'push' && github.ref == 'refs/heads/main' }}
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest,${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

This workflow:

- runs linting and tests on every push and pull request
- uses the official `astral-sh/setup-uv` action with caching for fast installs
- builds the Docker image on every run to catch build failures early
- pushes tagged images to GitHub Container Registry only on `main` branch
- tags images with both `latest` and the commit SHA for traceability
- uses GitHub Actions cache for faster Docker builds

You can adapt this to push to other registries like Docker Hub or AWS ECR by changing the login and registry configuration.

## How Deployment Differs by Target

The CI part stays fairly similar across all targets. The CD part changes.

### VPS

You might:

- build and push an image to a registry
- SSH into the server or trigger a pull-based update
- restart Docker Compose services

### AWS ECS/Fargate

You usually:

- push the image to ECR
- update the ECS task definition or service revision
- let ECS roll out new tasks behind a load balancer

### Fly.io

You often:

- deploy directly with `fly deploy`
- or build and deploy through the platform's container flow

The application code may stay the same, but the deployment handoff changes based on what the platform manages.

## Where Migrations Fit

Database migrations should be treated as an explicit part of the release flow.

That may happen:

- before switching traffic
- in a one-off deployment job
- as a dedicated admin task

Be careful about tying migrations blindly to app startup in all environments. It can be acceptable for small systems, but it becomes risky as deployments grow more complex.

## Common Mistakes

### Letting deployment happen before quality checks

Always validate the app first.

### Building different artifacts in different places

Try to keep the artifact path consistent so what passed CI resembles what gets deployed.

### Treating CI/CD as provider-specific too early

Start with generic quality and artifact stages. Then adapt the deploy stage per platform.

### Hiding release-critical logic in ad hoc scripts

Keep your release path visible and understandable. People should be able to explain how code becomes a running service.

## What You Should Have After This Step

By now, you should understand:

- what Continuous Integration checks should protect this app
- what Continuous Delivery means for a containerized Python service
- what an example pipeline looks like from lint to deploy
- how deployment differs across VPS, AWS ECS/Fargate, and Fly.io
- why migrations and image publishing should be explicit release concerns

Next, you will look at concrete deployment workflows for each target environment.

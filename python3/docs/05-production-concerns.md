# Production Concerns

This is the point where the app stops being just a development exercise. Production readiness is mostly about operational discipline: how the service is configured, how it starts, how it reports health, how it logs, and how it behaves when something goes wrong.

## Configuration and Environment Variables

A production Python service should read environment-specific values from configuration, not from hardcoded constants.

Typical settings include:

- application name
- debug flag
- database URL
- allowed origins
- secret keys
- external service endpoints

The important rule is simple: code is versioned with the app, configuration changes by environment.

That means local development, staging, and production can run the same application code while using different values for things like database hosts and credentials.

In practice, you will usually load env vars into a settings object rather than reading `os.environ` all over the codebase.

## Secrets Handling

Secrets are configuration, but they deserve special treatment.

Examples:

- database passwords
- API keys
- session signing secrets
- cloud credentials passed to workloads

Basic rules:

- do not commit secrets to git
- do not bake secrets into container images
- do not scatter secrets across shell history and random config files
- prefer platform-managed secret stores when available

For local development, a `.env` file can be acceptable if it is ignored by git. In production, you usually want secret injection from the deployment platform.

## Logging

Logs are your first line of visibility when the service misbehaves.

At minimum, your service should emit logs that help you answer:

- did the app start
- did a request fail
- did a dependency fail
- did a migration run
- what version is deployed

For containerized services, a strong default is writing structured or at least consistent logs to standard output and standard error. Then the platform can collect them.

Avoid designing a logging strategy that assumes local files are the primary source of truth. That breaks down quickly once the app runs in containers or managed platforms.

## Health Checks

Health checks are simple, but they are operationally important.

Your `/health` endpoint helps answer whether the service is alive enough for orchestration and routing decisions. In more mature systems, you may split health concerns into separate endpoints such as:

- liveness
- readiness
- deeper dependency checks

For this guide, a simple `/health` endpoint is enough to teach the deployment model. It will be used later by Docker, reverse proxies, load balancers, and platforms that need to know when the app is safe to receive traffic.

## Process Model and Workers

This is one of the most important Python-specific production topics.

In local development, you probably run:

```bash
uv run uvicorn app.main:app --reload
```

That command is for development convenience, not for the full production story.

In production, you usually care about:

- worker count
- concurrency model
- startup time
- graceful shutdown
- memory footprint
- signal handling inside containers or service managers

For an ASGI app, common patterns include:

- `uvicorn` directly for simpler deployments
- `gunicorn` with `uvicorn` workers for more explicit multi-worker process management

### Production Command Examples

For a straightforward deployment with `uvicorn`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

For more control using `gunicorn` with `uvicorn` workers:

```bash
uv add gunicorn
```

```bash
gunicorn app.main:app --bind 0.0.0.0:8000 --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

The `gunicorn` approach gives you:

- mature process supervision
- graceful worker restarts
- configurable timeouts
- signal handling for zero-downtime deployments

The worker count depends on your deployment target. A common starting point is `2 * CPU cores + 1`, but tune based on actual workload and memory constraints.

The exact command depends on the environment, but the key lesson is that Python services often make the process model more explicit than many Node apps do.

## Error Handling and Operational Readiness

A production-like app should fail in ways you can reason about.

That includes:

- returning useful HTTP status codes
- not leaking sensitive internal details in responses
- logging enough detail for operators
- distinguishing validation errors from internal failures
- surfacing startup failures early instead of silently degrading

Operational readiness also means thinking about lifecycle events:

- what happens if the database is down at startup
- what happens if a migration has not run
- what happens if configuration is missing
- what happens during shutdown while requests are in flight

You do not need a perfect resilience strategy on day one. You do need to make failure visible and understandable.

## What Usually Changes Between Local and Production

When people say "it works locally," they often mean:

- one process
- manual startup
- local files for config
- no real restart strategy
- no log aggregation
- no external health monitoring

Production changes all of that. The app becomes one component inside a larger system that expects predictable startup, stable networking, machine-readable logs, and clear health signals.

## Common Mistakes

### Using debug settings as a permanent default

Debug behavior is helpful locally and risky in production.

### Hiding configuration access throughout the codebase

Centralize settings so you can reason about what the app needs.

### Treating logs as an afterthought

When the app fails in a remote environment, logs become your fastest path to understanding what happened.

### Assuming the dev server is the production process model

It is not enough to know the app starts with `uvicorn --reload`. You need to understand how the service runs under real load and orchestration.

## What You Should Have After This Step

By now, you should understand:

- why configuration and environment variables are first-class concerns
- how secrets handling differs from normal config
- why logs should flow cleanly from containers and platforms
- why health checks matter operationally
- why `uvicorn` local usage is not the complete production process story
- how error handling affects operations, not just code cleanliness

Next, you will package the app into a container and run it in a more production-like local environment.

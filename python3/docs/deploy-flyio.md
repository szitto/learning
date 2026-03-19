# Deploy to Fly.io

Fly.io is useful in this guide because it gives you a managed deployment experience without hiding the application shape completely. You still think in terms of containers, ports, secrets, and health, but you do not have to directly manage a VPS or model as many AWS resources.

It is a good "curiosity" platform because it shows what gets easier when the platform absorbs more operational work.

## Why Fly.io Is Different

Compared with a VPS:

- less server management
- less manual reverse proxy setup
- easier app bootstrapping

Compared with AWS ECS/Fargate:

- fewer visible infrastructure resources
- simpler deployment flow for small apps
- less cloud architecture overhead for learning

## Launch the App

After installing the Fly.io CLI and authenticating, start with:

```bash
fly launch
```

This command helps initialize the app on the platform and generates deployment-related configuration such as `fly.toml`.

During setup, Fly.io will ask questions about:

- app name
- region
- internal port
- whether to create backing services

Your goal is to align those answers with the FastAPI container that listens on the app port used in your Docker image.

## Configure the App

The generated `fly.toml` describes how Fly.io should run your service.

Here is an example configuration for the FastAPI app:

```toml
app = 'python-production-guide'
primary_region = 'ams'

[build]

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = 'stop'
  auto_start_machines = true
  min_machines_running = 0

[checks]
  [checks.health]
    port = 8000
    type = 'http'
    interval = '10s'
    timeout = '2s'
    grace_period = '5s'
    method = 'GET'
    path = '/health'

[[vm]]
  memory = '512mb'
  cpu_kind = 'shared'
  cpus = 1
```

This configuration:

- sets the internal port to match the app's exposed port
- enforces HTTPS for all traffic
- configures health checks against the `/health` endpoint
- uses minimal resources appropriate for a learning deployment
- enables auto-stop to reduce costs when there is no traffic

Typical concerns include:

- internal port mapping
- process or service configuration
- health checks
- region preferences
- optional volume or machine settings

You should treat this file as the platform-specific runtime definition for Fly.io, similar in spirit to how an ECS task definition describes runtime behavior in AWS.

## Set Secrets

Inject secrets with:

```bash
fly secrets set DATABASE_URL=postgresql+psycopg://... APP_ENV=production
```

This is one of the conveniences of a more managed platform. You do not need to SSH into a server and manually create env files just to get a small app running.

You still need to know which values belong in runtime configuration, but the platform gives you a cleaner way to inject them.

## Deploy the Application

Deploy with:

```bash
fly deploy
```

That command handles the application deployment flow through the platform's model. Depending on your setup, Fly.io may build from your Dockerfile or from its own app detection flow.

After deployment, verify:

- the public URL responds
- the `/health` endpoint works
- logs are visible through the Fly.io tooling

## How Fly.io Changes the Operational Model

Fly.io removes some responsibilities that are very visible on a VPS.

You usually do not need to manually manage:

- server provisioning
- reverse proxy installation
- TLS termination setup in the same hands-on way

You still need to manage:

- app configuration
- secrets
- database strategy
- release behavior
- runtime expectations like ports and health checks

So the platform is simpler, but it does not remove the need to understand how the service behaves.

## How Fly.io Compares to VPS and Fargate

### Versus VPS

Fly.io removes a lot of direct machine ownership. That makes it faster to get something online, but you also learn less about the underlying Linux and reverse proxy layer.

### Versus AWS ECS/Fargate

Fly.io has a smaller conceptual footprint. You do not spend as much time learning registry, service, load balancer, VPC, and security-group concepts. That makes it easier to start, but less representative of large-enterprise cloud environments.

## Common Mistakes

### Treating managed deployment as magic

The platform helps, but you still need to know your app's startup command, port, config needs, and health expectations.

### Forgetting runtime configuration

Even with a simple platform, secrets and environment values still matter.

### Assuming platform convenience replaces application discipline

You still need tests, migrations, logging, and a sensible container image.

## What You Should Understand After This Step

By now, you should understand:

- how `fly launch` initializes a managed deployment target
- how `fly secrets set` injects runtime config
- how `fly deploy` ships the app
- how Fly.io abstracts infrastructure compared with VPS and AWS ECS/Fargate

At this point, you have seen the same Python service deployed through three different operational models. The final step is to make sure the docs stay consistent and tell one coherent story.

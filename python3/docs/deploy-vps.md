# Deploy to a VPS

Deploying to a VPS is the most educational path in this guide because you see nearly every moving part directly. You are responsible for the server, the runtime, the reverse proxy, the deployment flow, and the operational basics.

This is not the most automated path, but it teaches the clearest production mental model.

## Provision the Server

Start with a small Linux VPS from a provider such as Hetzner, DigitalOcean, Linode, or OVH. Ubuntu is a fine default for learning.

You should have:

- the server IP address
- an SSH user with sudo access
- a DNS record that can point your domain or subdomain to the server

Your first connection will look like:

```bash
ssh user@your-server-ip
```

Before deploying the app, do basic server setup:

- create a non-root user if needed
- install system updates
- configure the firewall
- confirm SSH key access works reliably

## Install Docker and Compose

Once the server is reachable, install Docker and the Docker Compose plugin.

The exact commands depend on the Linux distribution, but the end goal is simple: the server should be able to pull or build your app image and run a multi-container stack.

Verify installation with:

```bash
docker --version
docker compose version
```

At this point, the server is ready to run a stack that includes:

- the Python app container
- PostgreSQL if you are hosting it on the same machine for learning
- a reverse proxy container or host-level proxy

## Transfer Configuration

Your VPS needs project configuration, but not your entire development machine state.

At minimum, you typically move or define:

- the `compose.yaml` file
- environment variables or an env file
- image tags or pull configuration
- reverse proxy configuration

For a small setup, an env file on the server might be acceptable:

```env
APP_ENV=production
DATABASE_URL=postgresql+psycopg://app:strongpassword@db:5432/app
```

Keep that file out of git. On a VPS, secrets handling is often less elegant than on managed platforms, so be disciplined about file permissions and server access.

## Run the Application

Once Docker and config are in place, start the stack:

```bash
docker compose up -d
```

If the app image is built elsewhere and pushed to a registry, you may instead:

```bash
docker compose pull
docker compose up -d
```

This is one of the reasons VPS deployment is educational: you can see the exact relationship between the container image, configuration, ports, and running processes.

After startup, verify the containers:

```bash
docker compose ps
docker compose logs app
```

## Add a Reverse Proxy and TLS

You usually do not want the app container exposed directly on the public internet without a reverse proxy layer.

A reverse proxy such as Nginx or Caddy can handle:

- TLS termination
- domain routing
- forwarding traffic to the app container
- HTTP to HTTPS redirection

For learning, Caddy is attractive because HTTPS setup is simpler. Nginx is also a great choice if you want a more traditional setup.

The high-level flow is:

1. point DNS to the VPS
2. configure the reverse proxy for your domain
3. forward incoming traffic to the app container
4. enable automatic TLS or configure certificates manually

Once this is working, your public app endpoint should sit behind the proxy while the Python app remains on an internal Docker network or a non-public port.

## Operate the Service

Running the app once is not the same as operating it.

On a VPS, basic operations include:

- checking logs with `docker compose logs`
- checking container state with `docker compose ps`
- restarting services with `docker compose restart`
- pulling a new image and recreating containers during deploys
- confirming `/health` after each release

This is also where you start to care about backup and recovery questions, especially if PostgreSQL is on the same machine.

## A Simple Update Flow

A practical beginner-friendly release flow looks like this:

1. build and push a new image in CI
2. SSH to the server
3. pull the new image
4. run `docker compose up -d`
5. verify logs and the `/health` endpoint

This is not the most advanced rollout strategy, but it is enough to teach what a real deployment actually consists of.

## Where Env Files Live

On a VPS, it is common to keep env files in a deployment directory on the server, for example:

```text
/opt/python-production-guide/
|-- compose.yaml
|-- .env
```

Only trusted operators should have access to that directory.

## Port Exposure Model

A simple safe layout is:

- app container listens on `8000`
- database container listens on `5432` only inside the private Docker network if possible
- reverse proxy exposes ports `80` and `443` publicly

That means the app is reachable through the proxy, not by exposing the raw app container directly to the internet.

## Downtime Expectations

For a small VPS setup with Docker Compose, updates are usually low-downtime or brief-downtime rather than truly zero-downtime. That is acceptable for learning.

The key lesson is understanding the deployment flow. Later, managed platforms and more advanced orchestration systems improve rollout behavior.

## Common Mistakes

### Exposing the app directly without a reverse proxy

Use a proxy for TLS and public traffic handling.

### Storing secrets in the repo

Keep server-specific secrets on the server, not in version control.

### Treating the server like a snowflake

Write down the steps and configuration. If the server dies, you should be able to rebuild it.

### Running everything as root

Use a safer operational model with a normal user and controlled sudo access.

## What You Should Understand After This Step

By now, you should understand:

- what a VPS actually is in deployment terms
- how Docker Compose can run the app on a Linux server
- why a reverse proxy and TLS matter
- where configuration and secrets live in a self-managed environment
- how a basic update and verification flow works

Next, compare this hands-on model with AWS ECS/Fargate, where much of the server management disappears but the cloud resource model becomes more important.

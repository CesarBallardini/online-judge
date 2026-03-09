# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Docker Compose setup for running the DMOJ (Don Mills Online Judge) platform on Windows 11. DMOJ is a competitive programming platform that allows users to submit solutions to programming problems, which are then automatically judged against test cases.

## Architecture

The system consists of 7 containerized services orchestrated by Docker Compose:

1. **db (MariaDB 10.5)**: Primary database storing users, problems, submissions, and all platform data
2. **redis**: Cache layer for sessions and application caching
3. **site**: Django web application (main DMOJ platform) running on port 8080
4. **worker**: Celery background worker for async tasks (uses same image as site)
5. **bridged**: Judge bridge process -- relays communication between Django site and judge instances (ports 9999/9998)
6. **judge**: Code execution engine that compiles and runs submitted solutions in a sandboxed environment (runs with privileged mode for security isolation)
7. **nginx**: Reverse proxy serving static/media files and forwarding requests to the site

### Service Dependencies

- **site** depends on db and redis (waits for health checks)
- **worker** depends on db and redis (shares volumes with site)
- **bridged** depends on db and redis (runs `manage.py runbridged`)
- **judge** depends on bridged (connects to bridge on port 9999)
- **nginx** depends on site (proxies requests to it)

### Data Flow

- User submits code -> **nginx** -> **site** receives submission -> stored in **db**
- **bridged** picks up pending submissions and dispatches to **judge**
- **judge** executes code in sandbox -> reports results back through **bridged** -> **site** updates **db**
- **worker** handles async tasks (notifications, ranking updates, etc.) via **redis**/Celery
- **nginx** handles all external traffic, serves static/media files directly, proxies dynamic requests to **site**

## Key Commands

### Starting and Stopping

```bash
docker-compose up -d --build    # Start all services (build if needed)
docker-compose up -d            # Start without building
docker-compose down             # Stop all services
docker-compose down -v          # Stop and remove volumes (CAUTION: deletes all data)
```

### Viewing Logs

```bash
docker-compose logs -f              # Follow all service logs
docker-compose logs -f site         # Site logs
docker-compose logs -f bridged      # Bridge logs
docker-compose logs -f judge        # Judge logs
docker-compose logs --tail=100 site # Last 100 lines
```

### Service Management

```bash
docker-compose restart site
docker-compose up -d --build site           # Rebuild and restart
docker-compose exec site python manage.py <command>
docker-compose exec site bash
```

### Database Operations

```bash
docker-compose exec site python manage.py createsuperuser
docker-compose exec site python manage.py migrate
docker-compose exec site python manage.py makemigrations
docker-compose exec db mysql -u dmoj -p dmoj
```

### Static Files

```bash
docker-compose exec site python manage.py collectstatic --noinput
```

### Scheme Unit-Test Problems

```bash
./manage.sh deploy-scheme-problem <code>   # Deploy R5RS problem to judge
```

## Configuration

### Environment Variables (.env)

Copy `.env.example` to `.env` before first run.

**Critical variables:**
- `MYSQL_ROOT_PASSWORD`, `MYSQL_PASSWORD`: Database credentials
- `SECRET_KEY`: Django secret for signing sessions (must be unique in production)
- `JUDGE_KEY`: Authentication key for judge (must match admin panel Judges config)
- `BRIDGE_API_KEY`: API key for judge bridge communication

**Network variables:**
- `ALLOWED_HOSTS`: Comma-separated hostnames (e.g., `localhost,127.0.0.1`)
- `SITE_URL`: Full URL where site is accessible

### Docker Compose Structure

- **Volumes**: Database and Redis use named volumes; all other data uses bind mounts under `./data/`
- **Networks**: All services communicate via `dmoj_network` bridge network
- **Health Checks**: db, redis, site, and nginx have health checks; dependent services wait for healthy status
- **YAML Anchors**: Shared environment variables are defined once via `x-site-environment`

### Key Files

- `site/Dockerfile`: Python 3.11-slim, clones DMOJ source, installs deps, copies custom settings
- `site/dmoj/docker_settings.py`: Docker-specific Django settings (extends DMOJ's `settings.py`)
- `site/dmoj_urls.py`: URL config that includes `judge.urls`
- `site/requirements.txt`: Python dependencies
- `judge/Dockerfile`: Python 3.11-slim, installs `dmoj` judge package
- `judge/start-judge.sh`: Waits for bridge, generates judge.yml, starts dmoj CLI
- `judge/scheme_grader.py`: R5RS unit-test grader (deployed per-problem as `grader.py`)
- `config/mysql/my.cnf`: MariaDB configuration
- `mariadb/init/`: Database initialization scripts (charset, timezone)

### Nginx Configuration

- **nginx/nginx.conf**: Global settings (gzip, client_max_body_size 100M)
- **nginx/conf.d/default.conf**: Single server block -- proxies to site:8080, serves static/media from `/site/static/` and `/site/media/`

## Development Workflow

### Making Changes to the Site

1. Edit files in `site/` directory
2. Rebuild: `docker-compose up -d --build site`
3. Watch logs: `docker-compose logs -f site`

### Adding Python Dependencies

1. Add to `site/requirements.txt`
2. Rebuild: `docker-compose up -d --build site worker bridged`

### Port Access

- **80**: Nginx (main entry point)
- **8080**: Django dev server (direct access for debugging)
- **9999**: Bridge judge port (judges connect here)
- **9998**: Bridge Django port (site pushes updates here)

## Startup Sequence

1. **db** and **redis** start (health checks begin)
2. Once healthy, **site**, **worker**, and **bridged** start in parallel
3. **site** entrypoint waits for db, runs migrations (if `RUN_MIGRATIONS=true`), collects static, starts Django
4. **bridged** runs `manage.py runbridged`, listens on ports 9999/9998
5. **judge** waits for bridged:9999 to be reachable, then connects
6. **nginx** starts after site is running

## Common Issues

### Judge Not Connecting

- Verify `JUDGE_KEY` in `.env` matches the key in admin panel (Admin > Judges)
- Check bridge is running: `docker-compose logs -f bridged`
- Check judge logs: `docker-compose logs -f judge`

### Port 80 Already in Use

Change nginx port in `docker-compose.yml`: `"8000:80"`

### Database Connection Refused

- Wait for db health check: `docker-compose ps`
- Check db logs: `docker-compose logs -f db`

### Static Files Not Loading

```bash
docker-compose exec site python manage.py collectstatic --noinput
docker-compose restart nginx
```

## Problem Formats

### Standard (stdin/stdout)

Students write full programs with `(read)` and `(display)`. Test cases use `.in`/`.out` file pairs.

```
scheme-example/max-of-numbers/
├── init.yml          # test_cases with {in: 1.in, out: 1.out, points: N}
├── solution.rkt      # Reference solution (#lang racket, uses I/O)
├── 1.in / 1.out      # Test case pairs
└── ...
```

Deploy: `cp -r scheme-example/<code>/ data/problems/<code>/`

### Unit-test (R5RS)

Students submit pure function definitions (no `#lang`, no I/O). A custom grader loads them into an R5RS sandbox and runs teacher-written unit tests.

```
scheme-example/max-of-list/
├── init.yml          # custom_judge: grader.py + test_cases with {points: N}
├── tests.rkt         # (test "name" <expr> <expected>) forms
└── solution.rkt      # Reference R5RS solution (no #lang, no I/O)
```

Deploy: `./manage.sh deploy-scheme-problem <code>` (copies files + `judge/scheme_grader.py` as `grader.py`)

**Grader architecture**: `judge/scheme_grader.py` extends `StandardGrader`. At init, it replaces the student source with a `#lang racket` wrapper that creates an R5RS sandbox (`make-evaluator 'r5rs`), loads the student code, runs all tests, and outputs structured `RESULT:PASS/FAIL` lines. The grader runs the wrapper once on the first `grade(case)` call and caches results for subsequent calls.

**R5RS enforcement**: `#lang` stripping (rejects non-R5RS), sandbox evaluator (`#:allow-for-require '()`), per-expression resource limits (5s / 128MB).

**Problem time limit**: Set to 10+ seconds (`--time-limit 10`) due to ~2s sandbox startup overhead.

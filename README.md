# DMOJ Online Judge - Docker Setup

Docker Compose setup for running the [DMOJ](https://dmoj.ca) competitive programming platform on a local area network.

## Services

| Service | Description |
|---------|-------------|
| **db** | MariaDB 10.5 database |
| **redis** | Redis 7 cache and session store |
| **site** | Django web application (port 8080) |
| **worker** | Celery background task worker |
| **bridged** | Judge bridge (ports 9999/9998) -- relays between site and judges |
| **judge** | Code execution engine (privileged, sandboxed) |
| **nginx** | Reverse proxy (port 80), serves static/media files |

## Quick Start

```bash
# 1. First-time setup (generates secrets, builds, starts everything)
./manage.sh init

# 2. Access the site
# http://<HOST_IP>      (via nginx)
# http://<HOST_IP>:8080 (direct to Django)
```

Or manually:

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env -- set HOST_IP to your server's LAN IP and update passwords/keys

# 2. Build and start
./manage.sh start

# 3. Create admin account
./manage.sh create-admin
```

## Configuration

All configuration lives in `.env`. Key variables:

| Variable | Description |
|----------|-------------|
| `HOST_IP` | Your server's LAN IP (e.g. `192.168.0.3`). Drives `ALLOWED_HOSTS` and `SITE_URL` |
| `MYSQL_ROOT_PASSWORD` | MariaDB root password |
| `MYSQL_PASSWORD` | MariaDB application password |
| `SECRET_KEY` | Django signing key (generate with `openssl rand -hex 32`) |
| `JUDGE_NAME` | Judge identifier (must match admin panel) |
| `JUDGE_KEY` | Judge authentication key (must match admin panel) |
| `BRIDGE_API_KEY` | Bridge communication key |
| `ADMIN_API_KEY` | API key for bulk-load endpoints |
| `TIME_ZONE` | Server timezone (e.g. `America/Argentina/Buenos_Aires`) |

## Judge Setup

After the site is running, the judge must be registered in the database before it can authenticate.

### Option A: Admin Panel

1. Go to `http://<HOST_IP>/admin/`
2. Navigate to **Judges** > **Add Judge**
3. Set **Name** to the value of `JUDGE_NAME` in `.env` (e.g. `paradigmas`)
4. Set **Authentication key** to the value of `JUDGE_KEY` in `.env`
5. Save

### Option B: Django Shell

```bash
./manage.sh shell
```

```python
from judge.models import Judge
Judge.objects.create(
    name='paradigmas',           # must match JUDGE_NAME in .env
    auth_key='<JUDGE_KEY value from .env>',
    is_blocked=False
)
```

### Verify the Judge

```bash
# Check judge logs
./manage.sh logs -n 50 judge

# Check bridge logs
./manage.sh logs -n 50 bridged
```

You should see `Judge paradigmas authenticated` in the bridge logs. The judge will also appear as **online** in the admin panel under Judges, with its detected language executors (C, C++, Python, Java, etc.).

## Loading Teachers

Prepare a CSV file with the format:

```
username,password,email,first_name,last_name,organization
prof_garcia,,garcia@school.edu,Maria,Garcia,Paradigmas
prof_chen,,chen@school.edu,Wei,Chen,Paradigmas
```

- Leave `password` empty to auto-generate one
- `organization` must match an existing organization name

Then run:

```bash
# Validate first (no changes saved)
./manage.sh load-teachers teachers.csv --dry-run

# Import for real
./manage.sh load-teachers teachers.csv
```

Teachers are created as **staff** users with **organization admin** permissions.

## Loading Students

Prepare a CSV file with the format:

```
username,password,email,first_name,last_name,organization
jdoe,,jdoe@school.edu,John,Doe,Paradigmas
asmith,custompass123,asmith@school.edu,Alice,Smith,Paradigmas
```

Then run:

```bash
# Validate first
./manage.sh load-students students.csv --dry-run

# Import for real
./manage.sh load-students students.csv
```

## Loading Problems

Prepare a CSV file with the format:

```
code,name,description,time_limit,memory_limit,points,group
hello,Hello World,Write a program that prints "Hello World!",1.0,262144,1.0,Basics
sum2,Sum of Two Numbers,Read two integers and print their sum.,2.0,262144,2.0,Basics
```

Then run:

```bash
./manage.sh load-problems problems.csv --dry-run
./manage.sh load-problems problems.csv
```

After importing problem metadata, upload test cases via **Admin > Problems > Edit > Test Data**, or copy test data files directly into `data/problems/<problem_code>/`.

See `data/imports/*.example.csv` for template files.

## manage.sh Reference

```
Lifecycle:
  start             Build (if needed) and start all services
  stop              Stop all services (data preserved)
  restart [svc]     Restart all services, or a specific one
  rebuild [svc]     Rebuild and restart all or specific service
  status            Show service status and health
  destroy           Stop and remove all volumes (CAUTION: deletes data)

Logs:
  logs [svc]        Follow logs (all services or specific one)
  logs -n N [svc]   Show last N lines

Django:
  create-admin      Create a superuser account interactively
  migrate           Run database migrations
  collectstatic     Collect static files and restart nginx
  shell             Open Django interactive shell
  djcommand <cmd>   Run arbitrary manage.py command

Database:
  backup [file]     Dump database to SQL file (default: backup_YYYYMMDD_HHMMSS.sql)
  restore <file>    Restore database from SQL dump
  dbshell           Open MySQL shell

Setup:
  init              First-time setup: copy .env, generate secrets, build, start
  check             Run Django system checks

Data Import (REST API):
  load-students <csv>    Import students from CSV via API
  load-teachers <csv>    Import teachers from CSV via API (staff + org admin)
  load-problems <csv>    Import problems from CSV via API
  Append --dry-run to validate without saving

Debug:
  exec <svc> <cmd>  Run a command inside a service container
  health            Show health status of all services
```

## Volumes

- `dmoj_database` -- MariaDB data (named volume)
- `dmoj_redis_data` -- Redis persistence (named volume)
- `./data/static/` -- Collected static files
- `./data/media/` -- User uploads
- `./data/problems/` -- Problem test data (shared with judge)
- `./data/log/` -- Application logs

## Ports

| Port | Service | Purpose |
|------|---------|---------|
| 80 | nginx | Main entry point (LAN access) |
| 8080 | site | Direct Django access (debugging) |
| 9999 | bridged | Judge connection port |
| 9998 | bridged | Site-to-bridge push updates |

## Troubleshooting

**Port 80 in use:** Change nginx port in `docker-compose.yml` to e.g. `"8000:80"`

**Judge not connecting:** Verify `JUDGE_KEY` in `.env` matches the key registered in the admin panel. Check logs with `./manage.sh logs judge` and `./manage.sh logs bridged`.

**Static files missing:** Run `./manage.sh collectstatic`

**Changing server IP:** Update `HOST_IP` in `.env` and restart: `./manage.sh rebuild`

## References

- [DMOJ Documentation](https://docs.dmoj.ca/)
- [DMOJ Site Source](https://github.com/DMOJ/site)
- [DMOJ Judge Source](https://github.com/DMOJ/judge)

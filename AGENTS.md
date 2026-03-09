# AGENTS.md

Guidelines for AI coding agents working on this repository. Follows the [AGENTS.md specification](https://agents.md/).

## Project Overview

Containerized DMOJ online judge for LAN-based classroom use. Seven Docker services orchestrated by `docker-compose.yml`. All operations go through `manage.sh`.

## Repository Structure

```
online-judge/
├── docker-compose.yml          # 7-service orchestration
├── .env / .env.example         # Secrets and configuration
├── manage.sh                   # CLI entry point for all operations
├── site/                       # Django web application
│   ├── Dockerfile
│   ├── dmoj/docker_settings.py # Django settings for Docker
│   ├── dmoj_urls.py            # URL routing (imports dmoj.urls)
│   ├── requirements.txt
│   └── custom_commands/        # REST API + management commands
├── judge/                      # Code execution engine
│   ├── Dockerfile
│   ├── start-judge.sh          # Startup script (autoconf, judge.yml)
│   └── scheme_grader.py        # R5RS unit-test grader (canonical source)
├── scheme-example/             # Problem templates
│   ├── max-of-numbers/         # Standard format (stdin/stdout)
│   └── max-of-list/            # Unit-test format (R5RS)
├── nginx/                      # Reverse proxy configuration
├── config/mysql/               # MariaDB configuration
├── mariadb/init/               # DB initialization scripts
└── data/                       # Runtime data (bind-mounted)
    ├── problems/               # Deployed problem data
    └── imports/                # CSV import templates
```

## Build and Run

```bash
./manage.sh init            # First-time setup: .env, secrets, build, start
./manage.sh start           # Build and start all services
./manage.sh stop            # Stop all services (data preserved)
./manage.sh rebuild [svc]   # Rebuild and restart all or specific service
./manage.sh status          # Show service status and health
./manage.sh logs [svc]      # Follow logs
```

## Testing and Verification

```bash
./manage.sh check                        # Run Django system checks
./manage.sh health                       # Show health status of all services
docker-compose logs -f judge             # Watch judge execution logs
docker-compose logs -f bridged           # Watch bridge communication logs
```

## Code Style and Conventions

- **DMOJ URLs**: Always import from `dmoj.urls`, NOT `judge.urls`
- **manage.sh commands**: Add `cmd_<name>()` function, update `usage()`, add to `case` dispatch block
- **Docker env vars**: Use `x-site-environment` YAML anchors for shared variables
- **Secrets**: All in `.env`, never committed. Generate via `openssl rand -hex`
- **Python**: Site uses Python 3.11 with Django (DMOJ source)
- **Shell**: `manage.sh` uses bash with color-coded output (`info`, `warn`, `error` helpers)

## Problem Formats

### Standard (stdin/stdout)
- Location: `scheme-example/<code>/`
- Files: `init.yml` (with `in`/`out` refs), `.in`/`.out` pairs, `solution.rkt`
- Deploy: `cp -r scheme-example/<code>/ data/problems/<code>/`

### Unit-test (R5RS Scheme)
- Location: `scheme-example/<code>/`
- Files: `init.yml` (`custom_judge: grader.py`, points-only entries), `tests.rkt`, `solution.rkt`
- Deploy: `./manage.sh deploy-scheme-problem <code>`
- Grader source: `judge/scheme_grader.py` (canonical). Gets copied as `grader.py` into each problem directory
- Grader extends `StandardGrader`, replaces student source with a `#lang racket` wrapper at compile time
- Wrapper creates R5RS sandbox (`make-evaluator 'r5rs`), loads student code, runs tests, outputs `RESULT:PASS|name` or `RESULT:FAIL|name|detail` lines
- R5RS enforcement: `#lang` stripping, sandbox with `#:allow-for-require '()`, 5s/128MB per-expression limits
- `tests.rkt` format: `(test "name" <expr> <expected>)` — use `error` as expected to test for exceptions
- Problem time limit: 10+ seconds (sandbox startup ~2s)

## Common Tasks

### Adding a new unit-test problem

```bash
# 1. Create problem files
mkdir scheme-example/my-problem
# Write tests.rkt, init.yml, solution.rkt (see scheme-example/max-of-list/ for reference)

# 2. Ensure test count in tests.rkt matches entry count in init.yml
# 3. Points in init.yml must sum to 100
# 4. solution.rkt must be pure R5RS (no #lang, no I/O)

# 5. Deploy
./manage.sh deploy-scheme-problem my-problem

# 6. Create in Django
./manage.sh create-problem --code my-problem --name "My Problem" --time-limit 10 --languages RKT --group Scheme
```

### Modifying the grader

```bash
# 1. Edit the canonical source
#    judge/scheme_grader.py

# 2. Rebuild judge container
docker-compose up -d --build judge

# 3. Re-deploy affected problems
./manage.sh deploy-scheme-problem <code>
```

### Adding a manage.sh command

1. Add `cmd_<name>()` function in `manage.sh`
2. Add usage text to `usage()` under the appropriate `${CYAN}` section
3. Add entry to the `case` dispatch block at the bottom

## Security

- Never commit `.env` (contains secrets, DB passwords, API keys)
- Judge runs in privileged Docker mode for sandboxed code execution
- R5RS sandbox blocks filesystem access (`sandbox-path-permissions '()`) and module imports (`#:allow-for-require '()`)
- Student code is embedded as a string literal in the wrapper — escaping handles `\`, `"`, newlines, nulls

#!/usr/bin/env bash
set -e

# --- Colors -------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# --- Detect docker compose command --------------------------------------------
if docker compose version &>/dev/null; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
else
    error "Neither 'docker compose' nor 'docker-compose' found. Please install Docker."
    exit 1
fi

# --- Load .env if present ----------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# Defaults matching docker-compose.yml
MYSQL_DATABASE="${MYSQL_DATABASE:-dmoj}"
MYSQL_USER="${MYSQL_USER:-dmoj}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-dmoj_password}"
HOST_IP="${HOST_IP:-localhost}"
SITE_URL="http://${HOST_IP}"

# --- Usage --------------------------------------------------------------------
usage() {
    echo -e "${BOLD}Usage:${NC} ./manage.sh <command> [args]"
    echo ""
    echo -e "${CYAN}Lifecycle:${NC}"
    echo "  start             Build (if needed) and start all services"
    echo "  stop              Stop all services (data preserved)"
    echo "  restart [svc]     Restart all services, or a specific one"
    echo "  rebuild [svc]     Rebuild and restart all or specific service"
    echo "  status            Show service status and health"
    echo -e "  destroy           Stop and remove all volumes (${RED}CAUTION: deletes data${NC})"
    echo ""
    echo -e "${CYAN}Logs:${NC}"
    echo "  logs [svc]        Follow logs (all services or specific one)"
    echo "  logs -n N [svc]   Show last N lines"
    echo ""
    echo -e "${CYAN}Django:${NC}"
    echo "  create-admin      Create a superuser account interactively"
    echo "  migrate           Run database migrations"
    echo "  collectstatic     Collect static files and restart nginx"
    echo "  shell             Open Django interactive shell"
    echo "  djcommand <cmd>   Run arbitrary manage.py command"
    echo ""
    echo -e "${CYAN}Database:${NC}"
    echo "  backup [file]     Dump database to SQL file (default: backup_YYYYMMDD_HHMMSS.sql)"
    echo "  restore <file>    Restore database from SQL dump"
    echo "  dbshell           Open MySQL shell"
    echo ""
    echo -e "${CYAN}Setup:${NC}"
    echo "  init              First-time setup: copy .env, generate secrets, build, start"
    echo "  check             Run Django system checks"
    echo ""
    echo -e "${CYAN}Organizations:${NC}"
    echo "  add-org                Create an organization"
    echo "    --name <name>        Display name (required)"
    echo "    --slug <slug>        URL slug (required, lowercase, no spaces)"
    echo "    --short-name <name>  Short name / abbreviation (default: same as name)"
    echo ""
    echo -e "${CYAN}Users:${NC}"
    echo "  add-teacher            Create a teacher account (staff + org admin)"
    echo "    --username <user>    Login username (required)"
    echo "    --password <pw>      Password (auto-generated if omitted)"
    echo "    --email <email>      Email address"
    echo "    --first-name <name>  First name"
    echo "    --last-name <name>   Last name"
    echo "    --organization <slug> Organization to join as admin"
    echo ""
    echo -e "${CYAN}Problems:${NC}"
    echo "  create-problem         Create a problem in the database"
    echo "    --code <slug>        Problem code (required, must match folder in data/problems/)"
    echo "    --name <name>        Display name (required)"
    echo "    --description <txt>  Problem statement (default: 'Problem: <name>')"
    echo "    --time-limit <sec>   Time limit in seconds (default: 2.0)"
    echo "    --memory-limit <kb>  Memory limit in KB (default: 262144)"
    echo "    --points <pts>       Base points (default: 1.0)"
    echo "    --group <name>       Problem group/category (default: Uncategorized)"
    echo "    --languages <keys>   Comma-separated language keys (default: all)"
    echo "    --types <names>      Comma-separated type tags (e.g. Recursion,Lists,guia_1)"
    echo "    --private            Do not make the problem public"
    echo ""
    echo -e "${CYAN}Data Import (REST API):${NC}"
    echo "  load-students <csv>    Import students from CSV via API"
    echo "  load-teachers <csv>    Import teachers from CSV via API (staff + org admin)"
    echo "  load-problems <csv>    Import problems from CSV via API"
    echo "  Append --dry-run to validate without saving"
    echo ""
    echo -e "${CYAN}Debug:${NC}"
    echo "  exec <svc> <cmd>  Run a command inside a service container"
    echo "  health            Show health status of all services"
    echo ""
    echo -e "${CYAN}CSV Formats:${NC}"
    echo "  Students/Teachers: username,password,email,first_name,last_name,organization"
    echo "  Problems:          code,name,description,time_limit,memory_limit,points,group"
    echo "  See data/imports/*.example.csv for templates"
}

# --- Commands -----------------------------------------------------------------

cmd_start() {
    info "Building and starting all services..."
    $COMPOSE_CMD up -d --build
    info "All services started. Run './manage.sh status' to check health."
}

cmd_stop() {
    info "Stopping all services..."
    $COMPOSE_CMD down
    info "All services stopped. Data is preserved."
}

cmd_restart() {
    if [ -n "$1" ]; then
        info "Restarting service: $1"
        $COMPOSE_CMD restart "$1"
    else
        info "Restarting all services..."
        $COMPOSE_CMD restart
    fi
}

cmd_rebuild() {
    if [ -n "$1" ]; then
        info "Rebuilding and restarting service: $1"
        $COMPOSE_CMD up -d --build "$1"
    else
        info "Rebuilding and restarting all services..."
        $COMPOSE_CMD up -d --build
    fi
}

cmd_status() {
    $COMPOSE_CMD ps
}

cmd_destroy() {
    warn "This will stop all services and ${RED}DELETE ALL DATA${NC} (database, redis, volumes)."
    echo -n "Type 'yes' to confirm: "
    read -r confirm
    if [ "$confirm" = "yes" ]; then
        info "Destroying all services and volumes..."
        $COMPOSE_CMD down -v
        info "Done. All data has been removed."
    else
        info "Aborted."
    fi
}

cmd_logs() {
    local tail_lines=""
    local service=""

    # Parse -n N flag
    if [ "$1" = "-n" ]; then
        shift
        tail_lines="$1"
        shift
        service="$1"
    else
        service="$1"
    fi

    if [ -n "$tail_lines" ]; then
        if [ -n "$service" ]; then
            $COMPOSE_CMD logs --tail="$tail_lines" "$service"
        else
            $COMPOSE_CMD logs --tail="$tail_lines"
        fi
    else
        if [ -n "$service" ]; then
            $COMPOSE_CMD logs -f "$service"
        else
            $COMPOSE_CMD logs -f
        fi
    fi
}

cmd_create_admin() {
    info "Creating superuser account..."
    $COMPOSE_CMD exec site python manage.py createsuperuser
}

cmd_migrate() {
    info "Running database migrations..."
    $COMPOSE_CMD exec site python manage.py migrate
    info "Migrations complete."
}

cmd_collectstatic() {
    info "Collecting static files..."
    $COMPOSE_CMD exec site python manage.py collectstatic --noinput
    info "Restarting nginx..."
    $COMPOSE_CMD restart nginx
    info "Static files updated."
}

cmd_shell() {
    $COMPOSE_CMD exec site python manage.py shell
}

cmd_djcommand() {
    if [ -z "$1" ]; then
        error "Usage: ./manage.sh djcommand <command> [args...]"
        exit 1
    fi
    $COMPOSE_CMD exec site python manage.py "$@"
}

cmd_backup() {
    local file="${1:-backup_$(date +%Y%m%d_%H%M%S).sql}"
    info "Backing up database to ${BOLD}$file${NC}..."
    $COMPOSE_CMD exec -T db mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" > "$file"
    info "Backup saved to $file ($(wc -c < "$file" | tr -d ' ') bytes)."
}

cmd_restore() {
    if [ -z "$1" ]; then
        error "Usage: ./manage.sh restore <file.sql>"
        exit 1
    fi
    if [ ! -f "$1" ]; then
        error "File not found: $1"
        exit 1
    fi
    warn "This will overwrite the current database with the contents of ${BOLD}$1${NC}."
    echo -n "Type 'yes' to confirm: "
    read -r confirm
    if [ "$confirm" = "yes" ]; then
        info "Restoring database from $1..."
        $COMPOSE_CMD exec -T db mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" < "$1"
        info "Database restored."
    else
        info "Aborted."
    fi
}

cmd_dbshell() {
    $COMPOSE_CMD exec db mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"
}

cmd_init() {
    info "Starting first-time setup..."

    # 1. Copy .env
    if [ -f "$SCRIPT_DIR/.env" ]; then
        warn ".env already exists. Skipping copy."
    elif [ -f "$SCRIPT_DIR/.env.example" ]; then
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
        info "Copied .env.example to .env"
    else
        error ".env.example not found. Cannot proceed."
        exit 1
    fi

    # 2. Generate secrets
    if command -v openssl &>/dev/null; then
        info "Generating secret keys..."
        secret_key=$(openssl rand -hex 32)
        judge_key=$(openssl rand -hex 32)
        bridge_key=$(openssl rand -hex 32)
        sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$secret_key|" "$SCRIPT_DIR/.env"
        sed -i "s|^JUDGE_KEY=.*|JUDGE_KEY=$judge_key|" "$SCRIPT_DIR/.env"
        sed -i "s|^BRIDGE_API_KEY=.*|BRIDGE_API_KEY=$bridge_key|" "$SCRIPT_DIR/.env"
        info "Secret keys generated and written to .env"
    else
        warn "openssl not found. Please manually set SECRET_KEY, JUDGE_KEY, and BRIDGE_API_KEY in .env"
    fi

    # 3. Database passwords
    echo ""
    echo -n "Generate random database passwords? [Y/n]: "
    read -r gen_pw
    if [ "$gen_pw" != "n" ] && [ "$gen_pw" != "N" ]; then
        if command -v openssl &>/dev/null; then
            root_pw=$(openssl rand -hex 16)
            mysql_pw=$(openssl rand -hex 16)
            sed -i "s|^MYSQL_ROOT_PASSWORD=.*|MYSQL_ROOT_PASSWORD=$root_pw|" "$SCRIPT_DIR/.env"
            sed -i "s|^MYSQL_PASSWORD=.*|MYSQL_PASSWORD=$mysql_pw|" "$SCRIPT_DIR/.env"
            info "Database passwords generated."
        else
            warn "openssl not found. Please set passwords manually in .env"
        fi
    else
        echo -n "Enter MYSQL_ROOT_PASSWORD: "
        read -r root_pw
        echo -n "Enter MYSQL_PASSWORD: "
        read -r mysql_pw
        sed -i "s|^MYSQL_ROOT_PASSWORD=.*|MYSQL_ROOT_PASSWORD=$root_pw|" "$SCRIPT_DIR/.env"
        sed -i "s|^MYSQL_PASSWORD=.*|MYSQL_PASSWORD=$mysql_pw|" "$SCRIPT_DIR/.env"
    fi

    # 4. Build and start
    echo ""
    info "Building and starting all services..."
    # Re-source .env with new values
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
    $COMPOSE_CMD up -d --build

    # 5. Wait for health checks
    info "Waiting for services to become healthy..."
    local attempts=0
    local max_attempts=30
    while [ $attempts -lt $max_attempts ]; do
        if $COMPOSE_CMD ps | grep -q "(unhealthy)\|starting"; then
            sleep 5
            attempts=$((attempts + 1))
            echo -n "."
        else
            echo ""
            break
        fi
    done

    if [ $attempts -ge $max_attempts ]; then
        warn "Some services may not be healthy yet. Check with './manage.sh health'"
    else
        info "All services are up."
    fi

    # 6. Create superuser
    echo ""
    echo -n "Create a superuser account now? [Y/n]: "
    read -r create_su
    if [ "$create_su" != "n" ] && [ "$create_su" != "N" ]; then
        $COMPOSE_CMD exec site python manage.py createsuperuser
    fi

    echo ""
    info "Setup complete! Access the site at http://localhost"
}

cmd_check() {
    info "Running Django system checks..."
    $COMPOSE_CMD exec site python manage.py check
}

cmd_add_org() {
    info "Creating organization..."
    $COMPOSE_CMD exec -T site python manage.py add_organization "$@"
}

cmd_add_teacher() {
    info "Creating teacher..."
    $COMPOSE_CMD exec -T site python manage.py add_teacher "$@"
}

cmd_create_problem() {
    info "Creating problem..."
    $COMPOSE_CMD exec -T site python manage.py add_problem "$@"
}

cmd_load_data() {
    local endpoint="$1"
    local csv_file="$2"
    local dry_run="$3"

    if [ -z "$csv_file" ]; then
        error "Usage: ./manage.sh load-${endpoint} <csv_file> [--dry-run]"
        echo "  See data/imports/${endpoint}.example.csv for the expected format."
        exit 1
    fi

    if [ ! -f "$csv_file" ]; then
        error "File not found: $csv_file"
        exit 1
    fi

    if [ -z "$BEARER_TOKEN" ]; then
        info "Generating API token for admin user..."
        BEARER_TOKEN=$(docker-compose exec -T site python manage.py generate_api_token admin 2>/dev/null | tr -d '\r\n')
        if [ -z "$BEARER_TOKEN" ]; then
            error "Failed to generate API token. Make sure the 'admin' user exists."
            exit 1
        fi
    fi

    local url="${SITE_URL}/api/admin/load-${endpoint}/"
    if [ "$dry_run" = "--dry-run" ]; then
        url="${url}?dry_run=true"
    fi

    info "Uploading ${BOLD}${csv_file}${NC} to ${BOLD}${url}${NC}..."

    local http_response
    http_response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: Bearer ${BEARER_TOKEN}" \
        -F "file=@${csv_file}" \
        "$url" 2>&1)

    local http_body http_code
    http_body=$(echo "$http_response" | sed '$d')
    http_code=$(echo "$http_response" | tail -n1)

    # Pretty-print if jq is available, otherwise raw JSON
    if command -v jq &>/dev/null; then
        echo "$http_body" | jq .
    else
        echo "$http_body"
    fi

    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        info "Done (HTTP $http_code)."
    else
        error "Request failed (HTTP $http_code)."
        exit 1
    fi
}

cmd_exec() {
    if [ -z "$1" ] || [ -z "$2" ]; then
        error "Usage: ./manage.sh exec <service> <command> [args...]"
        exit 1
    fi
    local svc="$1"
    shift
    $COMPOSE_CMD exec "$svc" "$@"
}

cmd_health() {
    echo -e "${BOLD}Service Health Status${NC}"
    echo "-------------------------------------"

    # Get status for each defined service
    local services
    services=$($COMPOSE_CMD ps --format '{{.Service}}\t{{.State}}\t{{.Health}}' 2>/dev/null) || {
        # Fallback for older docker compose
        $COMPOSE_CMD ps
        return
    }

    if [ -z "$services" ]; then
        warn "No services running."
        return
    fi

    while IFS=$'\t' read -r name state health; do
        local color="$GREEN"
        local status_text="$state"

        if [ -n "$health" ] && [ "$health" != "" ]; then
            status_text="$state ($health)"
        fi

        case "$state" in
            running)
                case "$health" in
                    healthy)   color="$GREEN" ;;
                    unhealthy) color="$RED" ;;
                    starting)  color="$YELLOW" ;;
                    *)         color="$GREEN" ;;
                esac
                ;;
            exited|dead) color="$RED" ;;
            *)           color="$YELLOW" ;;
        esac

        printf "  %-12s ${color}%s${NC}\n" "$name" "$status_text"
    done <<< "$services"
}

# --- Command dispatch ---------------------------------------------------------
case "${1:-}" in
    start)          cmd_start ;;
    stop)           cmd_stop ;;
    restart)        shift; cmd_restart "$@" ;;
    rebuild)        shift; cmd_rebuild "$@" ;;
    status)         cmd_status ;;
    destroy)        cmd_destroy ;;
    logs)           shift; cmd_logs "$@" ;;
    create-admin)   cmd_create_admin ;;
    migrate)        cmd_migrate ;;
    collectstatic)  cmd_collectstatic ;;
    shell)          cmd_shell ;;
    djcommand)      shift; cmd_djcommand "$@" ;;
    backup)         shift; cmd_backup "$@" ;;
    restore)        shift; cmd_restore "$@" ;;
    dbshell)        cmd_dbshell ;;
    init)           cmd_init ;;
    check)          cmd_check ;;
    add-org)        shift; cmd_add_org "$@" ;;
    add-teacher)    shift; cmd_add_teacher "$@" ;;
    create-problem) shift; cmd_create_problem "$@" ;;
    load-students)  shift; cmd_load_data students "$@" ;;
    load-teachers)  shift; cmd_load_data teachers "$@" ;;
    load-problems)  shift; cmd_load_data problems "$@" ;;
    exec)           shift; cmd_exec "$@" ;;
    health)         cmd_health ;;
    --help|-h|"")   usage ;;
    *)
        error "Unknown command: $1"
        echo ""
        usage
        exit 1
        ;;
esac

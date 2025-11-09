#!/usr/bin/env bash
# Daily scheduled task for PythonAnywhere: pull latest code, install deps, run migrations, reload web app.
# Customize the variables in the CONFIG section below.
set -euo pipefail
IFS=$'\n\t'

######## CONFIG ########
# Your PythonAnywhere username
USERNAME="YOURUSERNAME"
# Project directory (absolute path)
APP_DIR="/home/${USERNAME}/MyCount"
# Virtualenv directory (absolute path)
VENV_DIR="${APP_DIR}/venv"
# Your webapp name (as shown in the Web tab domain, without https://)
WEBAPP_NAME="${USERNAME}.pythonanywhere.com"
# WSGI file path (shown at top of the Web tab)
WSGI_FILE="/var/www/${USERNAME}_pythonanywhere_com_wsgi.py"
# Optional: PythonAnywhere API token to reload via API (preferred). Leave empty to use touch fallback.
API_TOKEN=""
# Optional: env file with secrets: export DATABASE_URL=...; export SECRET_KEY=...
ENV_FILE="${APP_DIR}/env.sh"
########################

log() { printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }

reload_web() {
  if [[ -n "${API_TOKEN}" ]]; then
    log "Reloading web app via API: ${WEBAPP_NAME}"
    curl -s -X POST \
      -H "Authorization: Token ${API_TOKEN}" \
      "https://www.pythonanywhere.com/api/v0/user/${USERNAME}/webapps/${WEBAPP_NAME}/reload/" \
      | sed 's/.*/[api] &/' || true
  else
    log "Reloading web app by touching WSGI file: ${WSGI_FILE}"
    touch "${WSGI_FILE}"
  fi
}

log "Starting scheduled update in ${APP_DIR}"
cd "${APP_DIR}"

# Ensure git is present in PATH
command -v git >/dev/null 2>&1 || { log "git not found in PATH"; exit 1; }

log "Fetching origin/main"
 git fetch origin main
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [[ "${LOCAL}" == "${REMOTE}" ]]; then
  log "No changes detected. Exiting."
  exit 0
fi

log "Changes found. Pulling latest..."
 git pull --ff-only

# Install/upgrade dependencies quietly (if venv exists)
if [[ -d "${VENV_DIR}" ]]; then
  log "Installing dependencies in venv"
  "${VENV_DIR}/bin/pip" install -r requirements.txt -q || {
    log "pip install failed"; exit 1; }
else
  log "Virtualenv not found at ${VENV_DIR}, skipping pip install"
fi

# Load secrets (DATABASE_URL, SECRET_KEY, etc.) if provided
if [[ -f "${ENV_FILE}" ]]; then
  log "Loading environment from ${ENV_FILE}"
  # shellcheck disable=SC1090
  set -a; source "${ENV_FILE}"; set +a
else
  log "ENV_FILE not found, ensure your WSGI sets env vars or set them here"
fi

# Run migrations (use venv's flask if available)
log "Running migrations (flask db upgrade)"
FLASK_APP="backend.app:create_app" "${VENV_DIR}/bin/flask" db upgrade || {
  log "Migration failed"; exit 1; }

# Reload the web app
reload_web

log "Done."

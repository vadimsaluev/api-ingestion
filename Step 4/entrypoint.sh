#!/bin/bash

set -e

PID_FILE="/tmp/ingestion.pid"

start() {
  echo "Starting ingestion process..."

  python /app/data_pipeline.py \
    --url "${API_URL}" \
    --api-key "${API_KEY}" \
    --start-date "${START_DATE}" \
    --end-date "${END_DATE}" \
    --limit "${LIMIT}" \
    --output-dir "${OUTPUT_DIR}" \
    --bq-project "${BQ_PROJECT}" \
    --bq-dataset "${BQ_DATASET}" \
    --bq-table "${BQ_TABLE}" \
    --bq-credentials "${BQ_CREDENTIALS}" \
    --gdrive-path "${GDRIVE_PATH}" \
    --pg-host "${PG_HOST}" \
    --pg-port "${PG_PORT}" \
    --pg-db "${PG_DB}" \
    --pg-user "${PG_USER}" \
    --pg-password "${PG_PASSWORD}" \
    --pg-table "${PG_TABLE}" &

  echo $! > ${PID_FILE}
  wait $!
}

stop() {
  if [ -f ${PID_FILE} ]; then
    PID=$(cat ${PID_FILE})
    echo "Stopping ingestion process PID=${PID}"
    kill -TERM ${PID} || true
    rm -f ${PID_FILE}
  else
    echo "No running ingestion process found."
  fi
}

restart() {
  echo "Restarting ingestion process..."
  stop
  sleep 2
  start
}

case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    restart
    ;;
  *)
    echo "Usage: {start|stop|restart}"
    exit 1
    ;;
esac
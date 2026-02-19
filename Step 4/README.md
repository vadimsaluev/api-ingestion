For cost assumptions please refer to the root README.md file.

Environment variables to be put into entry point:
API_URL
API_KEY
START_DATE
END_DATE
LIMIT
OUTPUT_DIR

BQ_PROJECT
BQ_DATASET
BQ_TABLE
BQ_CREDENTIALS
GDRIVE_PATH

Important: Please note, that to persist output files outside the container, a drive mapping will be needed, which is not covered within this case study.

Exemplary run:

docker build -t ga-ingestion:latest .

docker run --rm \
  -e API_URL="https://your-API-URL" \
  -e API_KEY="your-API-key" \
  -e START_DATE="20160801" \
  -e END_DATE="20170801" \
  -e LIMIT="100" \
  -e OUTPUT_DIR="/raw_output" \
  -e BQ_PROJECT="my-use-case-analytics-project" \
  -e BQ_DATASET="my-use-case-bronze-layer" \
  -e BQ_TABLE="ga_sessions_raw" \
  -e BQ_CREDENTIALS="/home/user/keys/bq-service-account.json" \
  -e GDRIVE_PATH="gdrive://path-to-my-use-case-drive" \
  ga-ingestion:latest
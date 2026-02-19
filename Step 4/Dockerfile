FROM python:3.11-slim

# -------------------------
# System dependencies
# -------------------------

RUN apt-get update && apt-get install -y \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# -------------------------
# Working directory
# -------------------------

WORKDIR /app

# -------------------------
# Copy project files
# -------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY fetch_api_data.py .
COPY entrypoint.sh .

RUN chmod +x /app/entrypoint.sh

# -------------------------
# Environment defaults
# -------------------------

ENV PYTHONUNBUFFERED=1

# -------------------------
# Expose nothing (batch job)
# -------------------------

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["start"]
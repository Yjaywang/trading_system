# Stage 1: Build a virtual environment and install dependencies
FROM python:3.12-slim AS builder

WORKDIR /opt/venv

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

RUN python -m venv .
ENV PATH="/opt/venv/bin:$PATH"

# --no-cache-dir to save space
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Build the final image with the application code and virtual environment
FROM python:3.12-slim

WORKDIR /trading_system

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends supervisor git && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

COPY . .

ENV PATH="/opt/venv/bin:$PATH"


EXPOSE 8000
# EXPOSE 5555

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
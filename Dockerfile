FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends binutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENTRYPOINT ["python3", "compci.py"]

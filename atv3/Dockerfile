FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends binutils python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

CMD ["bash", "-c", "as --64 -o zeller.o zeller.s && ld -o zeller zeller.o && ./zeller"]

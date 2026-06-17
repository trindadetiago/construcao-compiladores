FROM debian:bookworm-slim

# binutils fornece as/ld (montar e linkar x86-64); python3 roda o compilador.
RUN apt-get update \
    && apt-get install -y --no-install-recommends binutils python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Por padrao roda a suite de testes (compila -> monta -> linka -> executa).
CMD ["bash", "test.sh"]

FROM python:3.8-slim as builder

WORKDIR /build

RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.8-slim

RUN apt-get update && apt-get install -y \
    chromium-driver \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

COPY app/ app/

RUN wget https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh \
    && chmod +x wait-for-it.sh

CMD ["./wait-for-it.sh", "mongo_db:27017", "--", "gunicorn", "--preload", "-k", "eventlet", "-w", "1", "--bind", "0.0.0.0:8000", "app.cmd.run:app"]

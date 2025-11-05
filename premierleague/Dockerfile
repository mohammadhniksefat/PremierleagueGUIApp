# ------------ Stage 1: Build/Compile ------------
FROM python:3.13.2-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
   ca-certificates openssl gcc g++ libpq-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip wheel setuptools
RUN pip install --no-build-isolation --no-cache-dir --prefix=/install -r requirements.txt

# ------------ Stage 2: Final Clean Image ------------
FROM python:3.13.2

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates openssl curl libssl-dev \
  && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY . /app

WORKDIR /app
CMD ["python", "main.py"]


FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    git \
    pkg-config \
    libboost-all-dev \
    libgl1 \
    libglib2.0-0 \
    libfreetype6 \
    libpng16-16 \
    libx11-6 \
    libxi6 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    cadquery-ocp \
    numpy \
    typing_extensions

WORKDIR /sandbox

RUN groupadd -r caduser && useradd -r -g caduser -m -d /sandbox caduser

COPY execute_cadquery.py /sandbox/execute_cadquery.py
RUN chmod +x /sandbox/execute_cadquery.py && \
    chown -R caduser:caduser /sandbox

USER caduser

VOLUME ["/sandbox/outputs"]

CMD ["python", "/sandbox/execute_cadquery.py"]

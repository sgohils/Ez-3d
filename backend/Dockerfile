FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-cache \
    curl \
    libgl1-mesa-glx \
    libglu1-mesa \
    libxrender1 \
    libsm6 \
    libegl1 \
    libglib2.0-0 \
    libxi6 \
    libxext6 \
    libxft2 \
    libfontconfig1 \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

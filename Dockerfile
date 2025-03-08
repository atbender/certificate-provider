FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libcairo2-dev \
    wget \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY assets/ ./assets/
COPY scripts/ ./scripts/

# install fonts
RUN chmod +x ./scripts/install_fonts.sh && ./scripts/install_fonts.sh

RUN mkdir -p /app/data

ENV PYTHONPATH=${PYTHONPATH}:/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

ENTRYPOINT ["python", "-m", "src.main"]

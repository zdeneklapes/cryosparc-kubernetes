FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT 8000
ENV EDITOR vim
EXPOSE 8000

WORKDIR /app
COPY requirements.txt /app/
RUN set -ex && \
    apt-get update &&  \
    apt-get -y install \
      vim \
      fish \
      python3-dev \
      bat \
      postgresql \
    --no-install-recommends && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    rm -rf /var/lib/apt/lists/*

CMD ["fish"]

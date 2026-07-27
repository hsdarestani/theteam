FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl ca-certificates && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/static/fonts \
    && curl -fL --retry 4 --retry-delay 2 \
      "https://raw.githubusercontent.com/google/fonts/main/ofl/notokufiarabic/NotoKufiArabic%5Bwght%5D.ttf" \
      -o /app/static/fonts/NotoKufiArabic-Variable.ttf \
    && test -s /app/static/fonts/NotoKufiArabic-Variable.ttf \
    && chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn","teamboard.wsgi:application","--bind","0.0.0.0:8000","--workers","3","--timeout","60","--access-logfile","-"]

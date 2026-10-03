FROM python:3.11-slim
WORKDIR /app
COPY requirements*.txt ./
RUN apt-get update && apt-get install -y --no-install-recommends g++ \
    && pip install --no-cache-dir -r requirements-build.txt \
    && pip install --no-cache-dir --no-build-isolation -r requirements.txt \
    && apt-get purge -y g++ && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
COPY app/ app/
COPY models/ models/
RUN useradd --create-home appuser
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import json,urllib.request; assert json.load(urllib.request.urlopen('http://localhost:8000/health'))['model_loaded']"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

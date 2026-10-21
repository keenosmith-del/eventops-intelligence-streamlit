FROM python:3.12.15-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY app.py pyproject.toml ./
COPY eventops ./eventops
COPY data ./data
COPY n8n ./n8n
COPY docs ./docs
COPY scripts ./scripts
COPY migrations ./migrations
COPY deploy ./deploy
COPY tests ./tests
COPY .streamlit/config.toml ./.streamlit/config.toml
RUN useradd --uid 1000 --create-home companion && mkdir -p /app/storage && chown -R companion:companion /app
ARG RELEASE_REVISION=development
LABEL org.opencontainers.image.revision=$RELEASE_REVISION
ENV RELEASE_REVISION=$RELEASE_REVISION
USER companion
EXPOSE 8501
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health',timeout=3)"
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--browser.gatherUsageStats=false"]

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY app.py ./
COPY eventops ./eventops
COPY data ./data
COPY n8n ./n8n
COPY docs ./docs
COPY .streamlit/config.toml ./.streamlit/config.toml
RUN useradd --create-home companion && mkdir -p /app/storage && chown -R companion:companion /app
USER companion
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--browser.gatherUsageStats=false"]

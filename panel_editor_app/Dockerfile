FROM python:3.11-slim

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip
COPY panel_editor_app/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application code
COPY panel_editor_app /app
WORKDIR /app

# Expose port (can be overridden via APP_PORT)
ENV APP_PORT=8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "${APP_PORT}"]
# Multi-stage build — minimal final image
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage — non-root, minimal
FROM python:3.11-slim

# Non-root user create
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

WORKDIR /app

# Copy only installed packages
COPY --from=builder /root/.local /home/appuser/.local
COPY app.py .

# Correct ownership
RUN chown -R appuser:appuser /app

# Non-root user switch
USER appuser

EXPOSE 8080

ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
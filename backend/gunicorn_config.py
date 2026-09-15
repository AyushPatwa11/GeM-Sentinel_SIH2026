"""Gunicorn configuration for FastAPI with Uvicorn workers."""
import multiprocessing
import os

# Get number of workers
workers = max(2, multiprocessing.cpu_count())

# Bind to port
bind = "0.0.0.0:8000"

# Worker class - use uvicorn worker
worker_class = "uvicorn.workers.UvicornWorker"

# Timeout
timeout = 120

# Preload app
preload_app = True

# Max requests to avoid memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

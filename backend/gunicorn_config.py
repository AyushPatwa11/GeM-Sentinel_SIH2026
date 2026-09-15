"""Gunicorn configuration for FastAPI with Uvicorn workers."""
import multiprocessing
import os

# Get number of workers - limit to 2 for free tier (512MB RAM)
workers = 2

# Bind to port
bind = "0.0.0.0:10000"

# Worker class - use uvicorn worker
worker_class = "uvicorn.workers.UvicornWorker"

# Timeout
timeout = 120

# Preload app
preload_app = False

# Max requests to avoid memory leaks
max_requests = 500
max_requests_jitter = 25

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

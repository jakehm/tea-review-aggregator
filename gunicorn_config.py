import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"
backlog = 2048

# Worker processes
workers = 1  # For free tier, use single worker
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

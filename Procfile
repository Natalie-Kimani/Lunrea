web: flask --app run.py db upgrade && gunicorn run:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120

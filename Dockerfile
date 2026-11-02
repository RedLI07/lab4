FROM python:3.12.7-slim
WORKDIR /app
COPY disk_check.py settings.json.example ./
USER 65534:65534
ENTRYPOINT ["python", "disk_check.py"]
CMD ["--config", "settings.json.example"]

FROM python:3.11-slim
WORKDIR /app
COPY mcp_stdio.py .
CMD ["python", "mcp_stdio.py"]

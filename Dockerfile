FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir ".[pdf]"
EXPOSE 8000
# Bind to all interfaces inside the container; publish the port with -p 8000:8000
CMD ["tone-and-gist", "serve", "--host", "0.0.0.0", "--port", "8000"]

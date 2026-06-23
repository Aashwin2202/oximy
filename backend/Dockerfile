FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    "fastapi>=0.115" "uvicorn[standard]>=0.30" "sqlalchemy>=2.0" \
    "psycopg[binary]>=3.2" "pydantic>=2.7" "pydantic-settings>=2.3"

COPY app ./app

COPY start.sh ./
RUN chmod +x start.sh

EXPOSE 8000
CMD ["./start.sh"]

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pytest \
    --cov=src \
    --cov-report=html:coverage_html \
    --cov-report=xml:coverage.xml \
    --junitxml=junit.xml \
    -v

CMD ["pytest", "--cov=src", "--cov-report=term-missing", "-v"]

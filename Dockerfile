FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN python -c "from pathlib import Path; p = Path('requirements.txt'); data = p.read_bytes(); enc = 'utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8'; Path('/tmp/requirements.txt').write_text(data.decode(enc), encoding='utf-8')" \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt

COPY . .

RUN mkdir -p data/processed outputs/charts outputs/evals

EXPOSE 8501

CMD ["python", "scripts/docker_start.py"]

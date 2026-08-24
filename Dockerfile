# Ourfeed has zero dependencies beyond the Python standard library, so
# there's nothing to `pip install` here, just copy the code and run it.
FROM python:3.12-alpine

WORKDIR /app
COPY . .

ENV OURFEED_PORT=8731
ENV OURFEED_DB_PATH=/app/data/ourfeed.db
EXPOSE 8731

CMD ["python", "ourfeed.py"]

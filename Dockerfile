FROM python:3.9-slim-buster

WORKDIR /app

COPY . .

# RUN pip install --no-cache-dir bs4 pandas python-dotenv requests py-cord
RUN pip install --no-cache-dir -r requirements.txt

# Deployment Command
CMD ["python", "./main.py"]
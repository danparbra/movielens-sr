FROM python:3.11
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
COPY artifacts/ ./artifacts/
EXPOSE 8000 8501
COPY start.sh ./
CMD ["bash", "start.sh"]
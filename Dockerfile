# Dùng Python base image
FROM python:3.10-slim

# Tạo thư mục làm việc trong container
WORKDIR /app

# Copy toàn bộ code vào container
COPY . .

# Cài các thư viện cần thiết
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000
EXPOSE 8000

# Chạy app với gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]

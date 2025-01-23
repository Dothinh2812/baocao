# Sử dụng Python 3.9 làm base image
FROM python:3.9-slim

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Sao chép requirements.txt vào container
COPY requirements.txt .

# Cài đặt các dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ code ứng dụng vào container
COPY . .

# Thiết lập biến môi trường
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Mở port 5000 để truy cập ứng dụng
EXPOSE 5000

# Chạy ứng dụng với gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app", "--workers", "3", "--timeout", "60"] 
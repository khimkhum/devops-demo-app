# Khiem Lab

Ứng dụng Flask dùng cho project DevOps internship.
Giao diện chuyển thể từ [Tooplate Neon Carbon](https://www.tooplate.com/view/2165-neon-carbon).
[Điều khoản sử dụng Tooplate](https://www.tooplate.com/about).

## Chạy trong Ubuntu WSL

```bash
cd /mnt/f/devops-intern-lab/devops-demo-app
source ~/.venvs/devops-demo/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Mở http://localhost:8000. Dừng bằng Ctrl+C.

## Thay cấu hình

```bash
APP_VERSION=v2 APP_ENV=staging python app.py
```

`/` trả HTML; `/health` và `/version` trả JSON.
Nút kiểm tra API gọi `/health` thật. Lịch sử chỉ lưu trong phiên trình duyệt.
Các phần Docker, CI, Kubernetes và GitOps chưa được triển khai.
Khi triển khai container sẽ dùng Gunicorn thay development server.

## Health check

Run: `bash scripts/check-health.sh http://127.0.0.1:8000`

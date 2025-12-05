# Quick Deploy (EC2, Ubuntu)

Goal: serve the prebuilt React app and run the FastAPI backend against the local SQLite DB with minimal steps and no Node.js on the server.

---

## 1) Build frontend locally (Windows)

```powershell
cd "C:\Users\gerri\Documents\Absa Stuff\NRD Dashboard\frontend"

# Build production bundle
npm run build

# Commit the build (it's gitignored, so force add)
cd ..
git add -f frontend/build
git commit -m "Production build"
git push origin main
```

---

## 2) First-time server setup (Ubuntu 22/24)

```bash
ssh -i your-key.pem ubuntu@your-server-ip

sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv nginx git

# Grab the code
cd /home/ubuntu
git clone https://github.com/GerritPotgieter/NRD-Dashboard.git nrd-dashboard
cd nrd-dashboard

# Python env (API + SQLite core)
python3 -m venv .venv
source .venv/bin/activate
pip install "fastapi==0.110.1" "uvicorn[standard]==0.27.1" "aiosqlite==0.19.0" "python-dotenv==1.0.1"

# Optional but recommended for screenshots/workflow: Playwright + Chromium + Chrome
pip install -r backend/requirements.txt
playwright install chromium
playwright install-deps chromium
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb
```

SQLite DB (`nrd_monitoring.db`) is created on first start; no external DB is required.

---

## 3) Systemd backend service

```bash
cd /home/ubuntu/nrd-dashboard
sudo cp deployment/nrd-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nrd-backend
sudo systemctl start nrd-backend
sudo systemctl status nrd-backend
```

Notes:

- Service expects the repo at `/home/ubuntu/nrd-dashboard` and the venv at `.venv/`.
- `.env` is optional; defaults allow all CORS. If you need to set `CORS_ORIGINS`, create `/home/ubuntu/nrd-dashboard/backend/.env` with `CORS_ORIGINS=*` (or a comma list).

---

## 4) Nginx + static frontend

```bash
# Copy site config and enable it
sudo cp /home/ubuntu/nrd-dashboard/deployment/nginx.conf /etc/nginx/sites-available/nrd-dashboard
sudo ln -sf /etc/nginx/sites-available/nrd-dashboard /etc/nginx/sites-enabled/nrd-dashboard
sudo rm -f /etc/nginx/sites-enabled/default

# Place the prebuilt frontend
sudo mkdir -p /var/www/nrd-dashboard
sudo cp -r /home/ubuntu/nrd-dashboard/frontend/build/* /var/www/nrd-dashboard/
sudo chown -R www-data:www-data /var/www/nrd-dashboard

sudo nginx -t && sudo systemctl restart nginx
```

The config proxies `/api/` to the backend on `127.0.0.1:8000` and serves the React build from `/var/www/nrd-dashboard`.

---

## 5) Quick verify

```bash
curl http://localhost:8000/api/domains       # backend
curl http://localhost/api/domains            # through nginx
```

Browser: `http://your-server-ip`

---

## 6) Update cycle (after code changes)

On Windows:

```powershell
cd "C:\Users\gerri\Documents\Absa Stuff\NRD Dashboard\frontend"
npm run build
cd ..
git add -f frontend/build
git commit -am "Update"
git push origin main
```

On server:

```bash
cd /home/ubuntu/nrd-dashboard
git pull
sudo cp -r frontend/build/* /var/www/nrd-dashboard/
sudo systemctl restart nrd-backend
sudo systemctl reload nginx
```

---

## 7) Optional extras (only if needed)

- Screenshots/workflow: `pip install -r backend/requirements.txt && playwright install chromium && playwright install-deps chromium`
- HTTPS: add certbot or your own certificate to the nginx server block.

That's it—no Node.js on the server, no external DB, minimal moving parts.

# Quick Deployment Steps

## 1. Build Frontend Locally (Windows)

```powershell
# Navigate to frontend
cd "C:\Users\gerri\Documents\Absa Stuff\NRD Dashboard\frontend"

# Build
npm run build

# Go back to root
cd ..

# Add build folder (it's in .gitignore, so use -f to force)
git add -f frontend/build

# Commit and push
git add .
git commit -m "Production build"
git push origin main
```

## 2. Deploy to Server

```bash
# SSH into server
ssh -i your-key.pem ubuntu@your-server-ip

# If first time, clone repo
git clone https://github.com/GerritPotgieter/NRD-Dashboard.git nrd-dashboard

# If updating
cd /home/ubuntu/nrd-dashboard
git pull

# Deploy frontend (copy built files to nginx directory)
sudo cp -r frontend/build/* /var/www/nrd-dashboard/

# Restart backend if needed
sudo systemctl restart nrd-backend
```

## 3. Verify

```bash
# Check backend
curl http://localhost:8000/api/domains

# Check frontend in browser
http://your-server-ip
```

---

## Daily Workflow

**When you make changes:**

1. Edit code on Windows
2. Build frontend: `npm run build` (in frontend directory)
3. Commit: `git add -f frontend/build && git commit -am "Update" && git push`
4. Deploy on server: `git pull && sudo cp -r frontend/build/* /var/www/nrd-dashboard/`

---

## Why This Works

- **No npm install on server**: Frontend is pre-built on Windows
- **Small git repo**: Only built files (~2-5 MB), not node_modules (~500 MB)
- **Fast deployment**: Just copy files, no compilation needed
- **No Node.js needed on server**: Only Python for backend

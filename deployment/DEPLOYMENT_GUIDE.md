# AWS EC2 Deployment Guide - Test Environment

## Instance Setup

### 1. Launch EC2 Instance

- **AMI**: Amazon Linux 2023
- **Instance Type**: t3.small (2 vCPU, 2GB RAM)
- **Storage**: 20GB gp3
- **Security Group**:
  - SSH (22) - Your IP only
  - HTTP (80) - 0.0.0.0/0
  - HTTPS (443) - 0.0.0.0/0

### 2. Connect via SSH

```bash
ssh -i your-key.pem ec2-user@your-ec2-ip
```

---

## Server Setup

### 3. Install Dependencies

```bash
# Update system
sudo dnf update -y

# Install Python, Nginx, Git
sudo dnf install -y python3-pip nginx git

# Install Node.js 20
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
sudo dnf install -y nodejs

# Install Chromium dependencies for Playwright
sudo dnf install -y \
    liberation-fonts \
    nss \
    libX11 \
    libXcomposite \
    libXdamage \
    libXext \
    libXrandr \
    libgbm \
    libdrm \
    libxcb \
    libxkbcommon \
    cups-libs \
    dbus-libs \
    at-spi2-atk \
    at-spi2-core \
    alsa-lib
```

### 4. Upload Your Code

From your Windows machine:

```powershell
# Using SCP (adjust paths)
scp -i your-key.pem -r "C:\Users\gerri\Documents\Absa Stuff\NRD Dashboard" ec2-user@your-ec2-ip:/home/ec2-user/

# Or use Git if you've pushed to a repo
git copy https://github.com/GerritPotgieter/NRD-Dashboard
```

On EC2, rename directory:

```bash
mv "/home/ec2-user/NRD Dashboard" /home/ec2-user/nrd-dashboard
```

### 5. Setup Python Environment

```bash
cd /home/ec2-user/nrd-dashboard

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Install Chrome for html2image
sudo dnf install -y google-chrome-stable

# Alternative if Chrome not available: Install Chromium
# sudo dnf install -y chromium
```

### 6. Create Environment Files

**Backend .env file** (in `backend/` directory):

```bash
cd /home/ec2-user/nrd-dashboard/backend
nano .env
```

Add your configuration:

```bash
# Use MONGO_URL not MONGODB_URI
MONGO_URL=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=your_database_name
CORS_ORIGINS=*

# Add your API keys
VIEW_DNS=your_viewdns_api_key
VIRUS_TOTAL=your_virustotal_api_key
SECURITY_TRAILS=your_securitytrails_api_key
DNS_DUMPSTER=your_dnsdumpster_api_key
WHOISFREAKS=your_whoisfreaks_api_key
```

**Copy backend .env to project root** (required for systemd service):

```bash
cp /home/ec2-user/nrd-dashboard/backend/.env /home/ec2-user/nrd-dashboard/.env
```

**Frontend .env file** (in `frontend/` directory):

```bash
cd /home/ec2-user/nrd-dashboard/frontend
nano .env
```

Add:

```bash
# Vite environment variables (VITE_ prefix required)
VITE_BACKEND_URL=
VITE_ENABLE_VISUAL_EDITS=false

# Legacy CRA compatibility (for existing code)
REACT_APP_BACKEND_URL=
REACT_APP_ENABLE_VISUAL_EDITS=false
```

**Note**: Leave `BACKEND_URL` empty to use relative URLs. Nginx will proxy `/api` requests to the backend.

### 7. Build Frontend (Vite)

```bash
cd /home/ec2-user/nrd-dashboard/frontend

# Install dependencies
npm install --legacy-peer-deps

# Build for production
npm run build

# Copy to web directory
sudo mkdir -p /var/www/nrd-dashboard
sudo cp -r build/* /var/www/nrd-dashboard/
sudo chown -R nginx:nginx /var/www/nrd-dashboard
```

**Vite produces a `build/` directory** with optimized static assets. This is smaller and faster than CRA builds.

---

## Configure Services

### 8. Backend Service (systemd)

```bash
sudo cp /home/ec2-user/nrd-dashboard/deployment/nrd-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nrd-backend
sudo systemctl start nrd-backend
sudo systemctl status nrd-backend
```

### 9. Nginx Configuration

```bash
sudo cp /home/ec2-user/nrd-dashboard/deployment/nginx.conf /etc/nginx/conf.d/nrd-dashboard.conf
sudo nginx -t  # Test config
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## Testing

### 10. Test Backend

```bash
# Test backend directly
curl http://localhost:8000/api/domains

# Test through Nginx
curl http://localhost/api/domains

# Both should return the same JSON response
```

### 11. Test Frontend

Open browser: `http://your-ec2-ip`

- Dashboard should load and display data
- Check browser console for any API errors

### 12. Run Workflow Manually (Optional)

To test the workflow that downloads NRD lists and captures screenshots:

```bash
cd /home/ec2-user/nrd-dashboard
source .venv/bin/activate
python main.py
```

---

## Maintenance Commands

### View Logs

```bash
# Backend logs
sudo journalctl -u nrd-backend -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

### Restart Services

```bash
sudo systemctl restart nrd-backend
sudo systemctl restart nginx
```

### Check Service Status

```bash
sudo systemctl status nrd-backend
sudo systemctl status nginx
```

### Manual Workflow Run

```bash
cd /home/ec2-user/nrd-dashboard
source .venv/bin/activate
python main.py
```

### Update Code

```bash
cd /home/ec2-user/nrd-dashboard
git pull  # If using git

# Rebuild frontend if you made frontend changes
cd frontend
npm run build
sudo cp -r build/* /var/www/nrd-dashboard/

# Restart backend if you made backend changes
sudo systemctl restart nrd-backend
```

---

## Vite Build Benefits

The migration to Vite provides several advantages for EC2 deployment:

### Faster Builds

- **Vite build time**: ~15-30 seconds
- **CRA build time**: ~60-120 seconds
- Reduces deployment time significantly

### Smaller Bundle Size

- Vite's tree-shaking and code-splitting produces smaller bundles
- Faster initial page load for users
- Lower bandwidth costs

### Better Development Experience

- Hot Module Replacement (HMR) is instant
- Dev server starts in milliseconds vs. 30+ seconds with CRA
- No more webpack compilation delays

### Production Optimizations

- Automatic code splitting by route
- Vendor chunk separation (React, UI libraries, charts)
- Modern ES modules for better browser caching
- Source maps disabled by default to save space

---

## Storage Management

### Check Disk Space

```bash
df -h
du -sh /home/ec2-user/nrd-dashboard/Domain_Downloads
du -sh /home/ec2-user/nrd-dashboard/Output
```

### Cleanup Old Files (7-day rolling window is automatic)

The workflow maintains 7 days of data automatically. No manual cleanup needed.

---

## Troubleshooting

### Backend won't start

```bash
sudo journalctl -u nrd-backend -n 50
# Check Python path and MongoDB connection
```

### Screenshots failing - "Could not find a Chrome executable"

```bash
# Install Chrome
sudo dnf install -y google-chrome-stable

# Or install Chromium as alternative
sudo dnf install -y chromium

# Also ensure Playwright is installed
cd /home/ec2-user/nrd-dashboard
source .venv/bin/activate
playwright install chromium
playwright install-deps chromium
```

### Out of memory

```bash
# Add swap space (temporary fix)
sudo dd if=/dev/zero of=/swapfile bs=1G count=2
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Consider upgrading to t3.medium
```

### Nginx 502 Bad Gateway

```bash
# Check if backend is running
sudo systemctl status nrd-backend
# Check SELinux (Amazon Linux)
sudo setsebool -P httpd_can_network_connect 1
```

---

## Cost Monitoring

Expected monthly costs:

- **EC2 t3.small**: ~$15/month
- **EBS 20GB**: ~$2/month
- **Data transfer**: ~$1/month
- **Total**: ~$18/month

Set up AWS Budget Alert:

- AWS Console → Billing → Budgets
- Create budget for $25/month with email alert at 80%

---

## Next Steps After Testing

Once you've verified everything works:

1. Create AMI snapshot for backup
2. Setup CloudWatch monitoring (optional)
3. Consider Elastic IP for static address
4. Implement S3 for screenshot storage
5. Setup automated backups
6. Deploy to work environment

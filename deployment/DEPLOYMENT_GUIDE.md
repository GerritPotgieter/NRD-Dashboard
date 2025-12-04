# Ubuntu Server Deployment Guide - Test Environment

## Instance Setup

### 1. Launch Server Instance

- **OS**: Ubuntu Server 22.04 LTS or 24.04 LTS
- **Instance Type**: 2 vCPU, 2GB RAM minimum (AWS t3.small, Azure B2s, or equivalent)
- **Storage**: 20GB SSD
- **Firewall/Security Group**:
  - SSH (22) - Your IP only
  - HTTP (80) - 0.0.0.0/0
  - HTTPS (443) - 0.0.0.0/0

### 2. Connect via SSH

```bash
ssh -i your-key.pem ubuntu@your-server-ip
```

---

## Server Setup

### 3. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python, Nginx, Git
sudo apt install -y python3-pip python3-venv nginx git curl

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Chromium dependencies for Playwright
sudo apt install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2
```

### 4. Upload Your Code

From your Windows machine:

```powershell
# Using SCP (adjust paths)
scp -i your-key.pem -r "C:\Users\gerri\Documents\Absa Stuff\NRD Dashboard" ubuntu@your-server-ip:/home/ubuntu/

# Or use Git if you've pushed to a repo
git clone https://github.com/GerritPotgieter/NRD-Dashboard
```

On Ubuntu server, rename directory:

```bash
mv "/home/ubuntu/NRD Dashboard" /home/ubuntu/nrd-dashboard
```

### 5. Setup Python Environment

```bash
cd /home/ubuntu/nrd-dashboard

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium
playwright install-deps chromium

# Install Chrome for html2image
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

# Alternative: Install Chromium instead
# sudo apt install -y chromium-browser
```

### 6. Create Environment Files

**Backend .env file** (in `backend/` directory):

```bash
cd /home/ubuntu/nrd-dashboard/backend
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
cp /home/ubuntu/nrd-dashboard/backend/.env /home/ubuntu/nrd-dashboard/.env
```

**Frontend .env file** (in `frontend/` directory):

```bash
cd /home/ubuntu/nrd-dashboard/frontend
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
cd /home/ubuntu/nrd-dashboard/frontend

# Install dependencies
npm install --legacy-peer-deps

# Build for production
npm run build

# Copy to web directory
sudo mkdir -p /var/www/nrd-dashboard
sudo cp -r build/* /var/www/nrd-dashboard/
sudo chown -R www-data:www-data /var/www/nrd-dashboard
```

**Vite produces a `build/` directory** with optimized static assets. This is smaller and faster than CRA builds.

---

## Configure Services

### 8. Backend Service (systemd)

```bash
sudo cp /home/ubuntu/nrd-dashboard/deployment/nrd-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nrd-backend
sudo systemctl start nrd-backend
sudo systemctl status nrd-backend
```

### 9. Nginx Configuration

```bash
sudo cp /home/ubuntu/nrd-dashboard/deployment/nginx.conf /etc/nginx/sites-available/nrd-dashboard
sudo ln -s /etc/nginx/sites-available/nrd-dashboard /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t  # Test config
sudo systemctl enable nginx
sudo systemctl restart nginx
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
cd /home/ubuntu/nrd-dashboard
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
cd /home/ubuntu/nrd-dashboard
source .venv/bin/activate
python main.py
```

### Update Code

```bash
cd /home/ubuntu/nrd-dashboard
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
du -sh /home/ubuntu/nrd-dashboard/Domain_Downloads
du -sh /home/ubuntu/nrd-dashboard/Output
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
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb

# Or install Chromium as alternative
sudo apt install -y chromium-browser

# Also ensure Playwright is installed
cd /home/ubuntu/nrd-dashboard
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

# Check backend logs
sudo journalctl -u nrd-backend -n 50

# Test backend directly
curl http://localhost:8000/api/domains
```

---

## Cost Monitoring

Expected monthly costs (AWS example):

- **EC2 t3.small**: ~$15/month
- **EBS 20GB**: ~$2/month
- **Data transfer**: ~$1/month
- **Total**: ~$18/month

For other cloud providers:

- **Azure B2s**: ~$30/month
- **DigitalOcean 2GB Droplet**: ~$18/month
- **Linode 4GB Shared**: ~$24/month

Set up billing alerts in your cloud provider's console.

---

## Next Steps After Testing

Once you've verified everything works:

1. Create server snapshot/backup for disaster recovery
2. Setup monitoring (optional - htop, netdata, or cloud provider monitoring)
3. Consider static IP address for consistent access
4. Setup automated backups (database and screenshots)
5. Configure UFW firewall if not using cloud provider security groups
6. Deploy to production environment

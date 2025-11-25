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
```

### 6. Create Environment File

```bash
nano /home/ec2-user/nrd-dashboard/.env
```

Add:

```bash
MONGODB_URI=your-mongodb-atlas-connection-string
ENVIRONMENT=production
```

### 7. Build Frontend

```bash
cd /home/ec2-user/nrd-dashboard/frontend
npm install
npm run build

# Copy to web directory
sudo mkdir -p /var/www/nrd-dashboard
sudo cp -r build/* /var/www/nrd-dashboard/
sudo chown -R nginx:nginx /var/www/nrd-dashboard
```

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

### 9. Daily Workflow Service & Timer

```bash
sudo cp /home/ec2-user/nrd-dashboard/deployment/nrd-daily.service /etc/systemd/system/
sudo cp /home/ec2-user/nrd-dashboard/deployment/nrd-daily.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nrd-daily.timer
sudo systemctl start nrd-daily.timer
sudo systemctl list-timers  # Verify scheduled
```

### 10. Nginx Configuration

```bash
sudo cp /home/ec2-user/nrd-dashboard/deployment/nginx.conf /etc/nginx/conf.d/nrd-dashboard.conf
sudo nginx -t  # Test config
sudo systemctl enable nginx
sudo systemctl start nginx
```

---

## Testing

### 11. Test Backend

```bash
curl http://localhost:8000/domains
```

### 12. Test Frontend

Open browser: `http://your-ec2-ip`

### 13. Test Daily Workflow (Manual Run)

```bash
sudo systemctl start nrd-daily.service
sudo journalctl -u nrd-daily.service -f
```

---

## Maintenance Commands

### View Logs

```bash
# Backend logs
sudo journalctl -u nrd-backend -f

# Daily workflow logs
sudo journalctl -u nrd-daily.service -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
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
sudo systemctl list-timers
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
sudo systemctl restart nrd-backend
```

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

### Screenshots failing

```bash
# Check Chromium dependencies
playwright install --with-deps chromium
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

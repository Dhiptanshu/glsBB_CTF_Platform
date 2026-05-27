# Deployment Guide: Oracle Cloud Free Tier

This guide walks you through deploying the GLS BB Platform ensuring security and performance on Oracle Cloud's Always Free tier.

## Prerequisites

1.  **Oracle Cloud Account**: Active account with access to Compute instances.
2.  **SSH Key Pair**: Generated on your local machine if not already done.
3.  **Domain Name (Optional)**: If you want HTTPS (highly recommended).

## Step 1: Prepare Application

### 1.1 Update Requirements
Ensure `gunicorn` is in `requirements.txt`.
```bash
echo "gunicorn" >> requirements.txt
```

### 1.2 Database Handling
- **SQLite (Current)**: Easiest. Just ensure the `instance` folder is writable.
- **PostgreSQL (Robust)**: Recommended for high concurrency, but adds setup complexity. We will stick to SQLite for now.

## Step 2: Create Compute Instance

### 2.1 Option A: The Quick Way (If it works)
Follow the standard wizard. If you get stuck on "Public IP" or "Private Subnet" warnings, stop and use **Option B**.

### 2.2 Option B: The Reliable Way (Create Network First)
If the instance wizard is glitchy, do this first:
1.  Open the **Hamburger Menu** -> **Networking** -> **Virtual Cloud Networks**.
2.  Click **"Start VCN Wizard"**.
3.  Select **"Create VCN with Internet Connectivity"**.
4.  Click **Start VCN Wizard**.
5.  **Name**: `gls-vcn`. Compartment: Default.
6.  Click **Next** -> **Create** -> **View VCN**.
7.  *Now* go back to **Compute** -> **Instances** -> **Create Instance**.
8.  In Networking, select **"Select existing virtual cloud network"** and choose `gls-vcn`.
    *   Select **"Select existing subnet"** -> choose the one that says **Public Subnet**.

1.  **Dashboard**: Go to "Compute" -> "Instances".
2.  **Create Instance**:
    *   **Name**: `gls-bb-server`
    *   **Image**: `Ubuntu 22.04` or `Canonical Ubuntu 24.04` (Minimal is fine).
    *   **Shape**: `VM.Standard.A1.Flex` (Ampere ARM) - **Highly Recommended** (4 OCPUs, 24GB RAM free tier). If unavailable, use `VM.Standard.E2.1.Micro` (AMD).
    *   **Network**: Select `gls-vcn` (if you used Option B) or "Create new VCN" (Option A). **Ensure "Assign Public IPv4" is YES.**

## Step 3: Configure Network (Oracle Firewall)

1.  Click on the **Subnet** link in the instance details.
2.  Click on the **Security List** (usually `Default Security List...`).
3.  **Add Ingress Rule**:
    *   **Source CIDR**: `0.0.0.0/0`
    *   **Protocol**: TCP
    *   **Destination Port Range**: `80, 443` (for Web) and `22` (for SSH, should be there).
    *   **Description**: Allow HTTP/HTTPS.

## Step 4: Server Setup (SSH into VM)

Connect via terminal:
```bash
ssh ubuntu@<YOUR_PUBLIC_IP> -i <path_to_private_key>
```

Run the following commands:
```bash
# Update System
sudo apt update && sudo apt upgrade -y

# Install Python & Nginx
sudo apt install python3-pip python3-venv nginx -y

# Clone/Upload Code (You can use git or scp)
# For now, let's assume you git clone or scp to ~/bb_platform
mkdir ~/bb_platform
```

## Step 5: Deploy Application

Navigate to app directory:
```bash
cd ~/bb_platform
# (Upload your files here)

# Setup Virtual Env
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5.1 Test Run
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
(Visit `http://<YOUR_IP>:8000` to test - requires port 8000 open in Security List temporarily).

### 5.2 Create Systemd Service (Keep it running)
Create `/etc/systemd/system/bb_platform.service`:
```ini
[Unit]
Description=Gunicorn instance to serve GLS BB Platform
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/bb_platform
Environment="PATH=/home/ubuntu/bb_platform/venv/bin"
ExecStart=/home/ubuntu/bb_platform/venv/bin/gunicorn --workers 4 --bind unix:bb_platform.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
```
Start it:
```bash
sudo systemctl start bb_platform
sudo systemctl enable bb_platform
```

## Step 6: Configure Nginx (Reverse Proxy)

Create `/etc/nginx/sites-available/bb_platform`:
```nginx
server {
    listen 80;
    server_name <YOUR_DOMAIN_OR_IP>;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/bb_platform/bb_platform.sock;
    }
}
```
Enable it & Restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/bb_platform /etc/nginx/sites-enabled
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl restart nginx
```
Open Firewall (OS Level):
```bash
sudo ufw allow 'Nginx Full'
```

## Maintenance & Updates

### How to Update the App (After code changes)
1.  **Local**: Make changes, verify, and verify `requirements.txt` if needed.
2.  **Local**: Run `python make_zip.py` to create `deploy.zip`.
3.  **Local**: Upload: `scp -i <KEY> deploy.zip ubuntu@<IP>:~/bb_platform/`
4.  **Server**: Receive and Unzip:
    ```bash
    ssh -i <KEY> ubuntu@<IP>
    cd ~/bb_platform
    unzip -o deploy.zip  # -o overwrites existing files
    ```
5.  **Server**: Restart Service to apply changes:
    ```bash
    sudo systemctl restart bb_platform
    ```

### How to Reset Admin Password (On Server)
If you need to change the admin password directly on the server:
1.  SSH into the server.
2.  Run these commands:
    ```bash
    cd ~/bb_platform
    source venv/bin/activate
    python3
    ```
3.  Inside Python shell:
    ```python
    from app import app, db, User
    with app.app_context():
        u = User.query.filter_by(username='admin').first()
        if u:
            u.set_password('YOUR_NEW_STRONG_PASSWORD')
            db.session.commit()
            print("Password updated!")
        else:
            print("User not found")
    exit()
    ```

## Done!
Visit your IP address.

# Docker Installation Guide for Windows

## Prerequisites
- Windows 10 64-bit: Pro, Enterprise, or Education (Build 19041 or higher)
- OR Windows 11 64-bit
- WSL 2 feature enabled (Docker Desktop will help you enable this)

## Installation Steps

### Step 1: Download Docker Desktop
1. Visit: https://www.docker.com/products/docker-desktop/
2. Click "Download for Windows"
3. Save the installer file (Docker Desktop Installer.exe)

### Step 2: Install Docker Desktop
1. **Run the installer** (Docker Desktop Installer.exe)
2. **Follow the installation wizard**:
   - Accept the license agreement
   - Choose "Use WSL 2 instead of Hyper-V" (recommended)
   - Click "Install"
3. **Wait for installation** to complete (may take 5-10 minutes)
4. **Restart your computer** when prompted

### Step 3: Start Docker Desktop
1. **Launch Docker Desktop** from Start Menu
2. **Accept the Docker Subscription Service Agreement**
3. **Wait for Docker Engine to start** (you'll see "Docker Desktop is running" in the system tray)
4. **Verify installation** by opening PowerShell and running:
   ```powershell
   docker --version
   docker compose version
   ```

### Step 4: Configure Docker (Optional but Recommended)
1. **Right-click Docker icon** in system tray
2. **Go to Settings**:
   - **Resources > Advanced**: Allocate at least 4GB RAM and 2 CPUs
   - **General**: Enable "Start Docker Desktop when you log in"

## Troubleshooting

### Issue: WSL 2 Installation Required
If you see an error about WSL 2:
1. Open PowerShell as Administrator
2. Run: `wsl --install`
3. Restart your computer
4. Start Docker Desktop again

### Issue: Virtualization Not Enabled
If you see virtualization errors:
1. Restart computer and enter BIOS/UEFI settings (usually F2, F10, or Del key)
2. Enable "Intel VT-x" or "AMD-V" (virtualization technology)
3. Save and exit BIOS
4. Start Docker Desktop

### Issue: Docker Desktop Won't Start
1. Check Windows version: `winver` (must be Build 19041+)
2. Update Windows to latest version
3. Reinstall Docker Desktop

## Verification

After installation, verify Docker is working:

```powershell
# Check Docker version
docker --version

# Check Docker Compose version
docker compose version

# Test Docker with hello-world
docker run hello-world

# Check Docker is running
docker ps
```

## Next Steps

Once Docker is installed and running:

1. **Navigate to project directory**:
   ```powershell
   cd "C:\Users\Durga prasad\Downloads\new"
   ```

2. **Start the chatbot system**:
   ```powershell
   docker compose up --build
   ```

3. **Access the services**:
   - Auth Service: http://localhost:8000/docs
   - Chat Service: http://localhost:8001/docs
   - RAG Service: http://localhost:8002/docs
   - Document Service: http://localhost:8003/docs
   - Notification Service: http://localhost:8004/docs
   - Admin Service: http://localhost:8005/docs
   - Analytics Service: http://localhost:8006/docs

## Alternative: Docker Desktop Alternatives

If Docker Desktop doesn't work, you can try:
- **Rancher Desktop**: https://rancherdesktop.io/
- **Podman Desktop**: https://podman-desktop.io/

## Need Help?

If you encounter issues:
1. Check Docker Desktop logs: Settings > Troubleshoot > View logs
2. Visit Docker documentation: https://docs.docker.com/desktop/windows/
3. Docker community forums: https://forums.docker.com/

---

**Estimated Installation Time**: 15-30 minutes (including download and restart)

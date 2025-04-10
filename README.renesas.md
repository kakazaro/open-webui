# Product Deployment

## Running Docker Containers

### Start Containers
Use `docker-compose` to bring up the containers in detached mode:

```bash
docker compose -f docker-compose.renesas.yaml up -d --build
```  

### Stop Containers
To bring down the running containers, use:

```bash
docker compose -f docker-compose.renesas.yaml down
```  

# Product Backup/Restore

### To backup data

```bash
docker run --rm -v web-openui_open-webui:/volume -v $(pwd):/backup busybox sh -c "cd /volume && tar cvf /backup/open-webui-backup.tar ."
```  
Backup file created at "open-webui-backup.tar"

### To restore data

Go to folder where "open-webui-backup.tar" is
```bash
docker run --rm -v web-openui_open-webui:/volume -v $(pwd):/backup busybox sh -c "cd /volume && tar xvf /backup/open-webui-backup.tar"
```  

# Local Development

For local development, follow these steps:

### Backend setup (option 1)

1. **Clone the Docker Compose File**
    - Copy `docker-compose.renesas.yaml` to `docker-compose.local.yaml`.
    - Modify the exposed port to `8080` to avoid conflicts.

2. **Run Web Backend Instance**
    - Start the backend using the modified `docker-compose.local.yaml`.

### Backend setup (option 2)

Required **Python 3.11**

1. **Go to `/backend` dir and run**
   ```bash
   cd ./backend
   ```  

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt -U
   ```  

3. **Start the backend:**
   ```bash
   uvicorn open_webui.main:app --port 8080 --host 0.0.0.0 --forwarded-allow-ips '*' --reload
   ```  

### Web Frontend

1. **Run Web Frontend**
    - NodeJS version: 22.x.x
    - Start the frontend using:
   ```bash
   npm run dev
   ```
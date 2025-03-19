# Product Deployment

## Build and Push Docker Image

### Build the Docker Image
Run the following command to build the Docker image using the `Dockerfile.renesas`:

```bash
docker build -f Dockerfile.renesas -t kakazaro/open-webui:latest .
```  

### Push the Docker Image
After building the image, push it to the repository:

```bash
docker push kakazaro/open-webui:latest
```  

## Running Docker Containers

### Start Containers
Use `docker-compose` to bring up the containers in detached mode:

```bash
docker compose -f docker-compose.renesas.yaml up -d
```  

### Stop Containers
To bring down the running containers, use:

```bash
docker compose -f docker-compose.renesas.yaml down
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

1. **Go to /backend dir and run**
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
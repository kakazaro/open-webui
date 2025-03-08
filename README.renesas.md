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

1. **Clone the Docker Compose File**
    - Copy `docker-compose.renesas.yaml` to `docker-compose.local.yaml`.
    - Modify the exposed port to `8080` to avoid conflicts.

2. **Run Web Backend Instance**
    - Start the backend using the modified `docker-compose.local.yaml`.

3. **Run Web Frontend**
    - Start the frontend using:

   ```bash
   npm run dev
   ```
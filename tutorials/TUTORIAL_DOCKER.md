# Docker Tutorial for Stirling Chat Project

## 📚 What is Docker?

Docker is like a **shipping container for software**. It packages your app with everything it needs (code, libraries, settings) so it runs the same everywhere.

| Without Docker | With Docker |
|----------------|-------------|
| "Works on my machine" problems | Works everywhere the same |
| Install Python, Node, PostgreSQL manually | Everything bundled together |
| Different versions cause conflicts | Isolated environments |

---

## 🔧 Part 1: Docker Basics

### 1.1 Check if Docker is Installed
```bash
docker --version
docker-compose --version
```
If not installed, download **Docker Desktop** from: https://www.docker.com/products/docker-desktop/

### 1.2 Key Concepts

| Term | What it means | Real-world analogy |
|------|---------------|-------------------|
| **Image** | Blueprint/recipe | Cookie cutter |
| **Container** | Running instance | Actual cookie |
| **Dockerfile** | Instructions to build image | Recipe card |
| **docker-compose.yml** | Multi-container setup | Full meal plan |
| **Volume** | Persistent storage | External hard drive |

---

## 📁 Part 2: Your Project's Docker Setup

### 2.1 Current Docker Files in Your Project

```
stirling_chat/
├── docker-compose.yml          # Defines PostgreSQL database
├── frontend/
│   ├── Dockerfile              # Builds React frontend
│   └── docker-compose.yml      # Runs frontend container
```

### 2.2 Understanding docker-compose.yml (Database)

Your main `docker-compose.yml`:
```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16    # Pre-built PostgreSQL + pgvector
    container_name: stirling_chat_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: stirling_chat
    ports:
      - "5433:5432"                   # Host:Container port mapping
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Persist data

volumes:
  postgres_data:
```

### 2.3 Understanding Dockerfile (Frontend)

Your `frontend/Dockerfile`:
```dockerfile
FROM node:20-alpine          # Start with Node.js base image

WORKDIR /app                 # Set working directory

COPY package.json ./         # Copy package.json first
RUN npm install              # Install dependencies

COPY . .                     # Copy all source code

EXPOSE 3000                  # Document which port app uses

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]  # Start command
```

---

## 🚀 Part 3: Essential Docker Commands

### 3.1 Container Management

```bash
# Start containers (from docker-compose.yml)
docker-compose up

# Start in background (detached mode)
docker-compose up -d

# Stop containers
docker-compose down

# Stop and remove volumes (DELETES DATA!)
docker-compose down -v
```

### 3.2 View Running Containers

```bash
# List running containers
docker ps

# List ALL containers (including stopped)
docker ps -a

# Example output:
# CONTAINER ID   IMAGE                    STATUS         NAMES
# abc123         pgvector/pgvector:pg16   Up 2 hours     stirling_chat_db
# def456         stirling_frontend        Up 1 hour      stirling_frontend
```

### 3.3 Container Logs

```bash
# View logs
docker logs stirling_chat_db

# Follow logs in real-time
docker logs -f stirling_chat_db

# Last 50 lines
docker logs --tail 50 stirling_chat_db
```

### 3.4 Restart Containers

```bash
# Restart a specific container
docker restart stirling_chat_db
docker restart stirling_frontend

# Restart all containers in compose file
docker-compose restart
```

### 3.5 Execute Commands Inside Container

```bash
# Open shell inside container
docker exec -it stirling_chat_db bash

# Run PostgreSQL command
docker exec -it stirling_chat_db psql -U postgres -d stirling_chat

# Example: Check tables
docker exec -it stirling_chat_db psql -U postgres -d stirling_chat -c "\dt"
```

---

## 🏗️ Part 4: Building Images

### 4.1 Build from Dockerfile

```bash
# Build image (run from folder with Dockerfile)
cd frontend
docker build -t stirling-frontend .

# Build with specific name and tag
docker build -t stirling-frontend:v1.0 .
```

### 4.2 List Images

```bash
docker images

# Example output:
# REPOSITORY          TAG       SIZE
# stirling-frontend   latest    500MB
# pgvector/pgvector   pg16      400MB
# node                20-alpine 180MB
```

### 4.3 Remove Images

```bash
# Remove specific image
docker rmi stirling-frontend

# Remove all unused images
docker image prune
```

---

## 💾 Part 5: Volumes (Data Persistence)

### 5.1 Why Volumes Matter

Without volumes, data is lost when container stops!

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect stirling_chat_postgres_data

# Remove volume (DELETES DATA!)
docker volume rm stirling_chat_postgres_data
```

### 5.2 Backup Database

```bash
# Export database to file
docker exec stirling_chat_db pg_dump -U postgres stirling_chat > backup.sql

# Import database from file
docker exec -i stirling_chat_db psql -U postgres stirling_chat < backup.sql
```

---

## 🔗 Part 6: Networking

### 6.1 Port Mapping

Format: `HOST_PORT:CONTAINER_PORT`

```yaml
ports:
  - "5433:5432"   # Access container's 5432 via localhost:5433
  - "3000:3000"   # Same port on both
  - "8080:80"     # Access container's 80 via localhost:8080
```

### 6.2 Container Communication

Containers in same docker-compose can talk using service names:
```yaml
services:
  backend:
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/stirling_chat
      #                                            ^^^^^^^^ service name, not localhost!
  postgres:
    # ...
```

---

## 📋 Part 7: Quick Reference Card

| Command | What it does |
|---------|--------------|
| `docker-compose up -d` | Start all services |
| `docker-compose down` | Stop all services |
| `docker ps` | List running containers |
| `docker logs <name>` | View container logs |
| `docker restart <name>` | Restart container |
| `docker exec -it <name> bash` | Shell into container |
| `docker build -t <name> .` | Build image |
| `docker images` | List images |

---

## 🎯 Exercise: Practice with Your Project

### Exercise 1: Check Your Running Containers
```bash
docker ps
```
You should see `stirling_chat_db` and `stirling_frontend`

### Exercise 2: View Database Logs
```bash
docker logs stirling_chat_db
```

### Exercise 3: Connect to Database
```bash
docker exec -it stirling_chat_db psql -U postgres -d stirling_chat

# Inside psql, try:
\dt                          # List tables
SELECT COUNT(*) FROM chunks; # Count chunks
\q                           # Exit
```

### Exercise 4: Restart Frontend After Code Changes
```bash
docker restart stirling_frontend
```

### Exercise 5: Backup Your Database
```bash
docker exec stirling_chat_db pg_dump -U postgres stirling_chat > stirling_backup.sql
```

---

## 🆘 Common Problems & Solutions

### Problem: "Port already in use"
```bash
# Find what's using the port
netstat -ano | findstr :5433

# Change port in docker-compose.yml
ports:
  - "5434:5432"  # Use different host port
```

### Problem: "Container keeps restarting"
```bash
# Check logs for errors
docker logs stirling_chat_db
```

### Problem: "Cannot connect to database"
```bash
# Make sure container is running
docker ps

# Check if port is correct in your .env
# POSTGRES_PORT=5433 (not 5432!)
```

### Problem: "Out of disk space"
```bash
# Clean up unused Docker resources
docker system prune -a
```

---

**Next:** Read `TUTORIAL_DEPLOYMENT.md` for deployment instructions.

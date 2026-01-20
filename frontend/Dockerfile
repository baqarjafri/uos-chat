# ============================================
# LOCAL DEVELOPMENT DOCKERFILE
# For local Docker Compose development only
# For Railway deployment, use Dockerfile.railway
# ============================================
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies with clean install
RUN npm ci

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start dev server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

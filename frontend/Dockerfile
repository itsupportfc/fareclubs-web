# ============================
# Build stage
# ============================
FROM node:22-alpine AS build

# Set the working directory inside the container
WORKDIR /app

# Copy dependency manifests first for layer caching
COPY package*.json ./

# Install dependencies using package-lock.json
# npm install => using package.josn => may change dependecies hence not used in prodcution
RUN npm ci

# Copy the rest of the frontend source code
COPY . .

# Run the Vite production build → outputs to /app/dist
RUN npm run build



# ============================
# Runtime (serve) stage
# ============================
FROM nginx:stable-alpine

# Remove default nginx configuration (optional, keeps things clean)
RUN rm -rf /etc/nginx/conf.d/*

# Copy build output from the previous stage into Nginx's web root
COPY --from=build /app/dist /usr/share/nginx/html

# (optional) Copy a custom nginx.conf if you have one
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose container port 80 (used internally in docker-compose)
EXPOSE 80

# Force Nginx to run in the foreground ( by default runs in background )
CMD ["nginx", "-g", "daemon off;"]

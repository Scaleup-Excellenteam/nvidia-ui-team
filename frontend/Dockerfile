FROM node:22-alpine AS base
WORKDIR /app

# Install deps (with caching)
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund

# Copy rest of the source
COPY . .

# Build
RUN npm run build

EXPOSE 3000

ENV PORT=3000 \
    NODE_ENV=production

CMD ["npm", "start"]



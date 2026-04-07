# Multi-stage Dockerfile for Digital FTE Frontend (Next.js)
# Optimized for production with minimal image size

# Stage 1: Dependencies
FROM node:18-alpine AS deps

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production --prefer-offline

# Stage 2: Builder
FROM node:18-alpine AS builder

WORKDIR /app

# Copy dependencies and source code
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/package*.json ./
COPY frontend/tsconfig.json ./
COPY frontend/next.config.* ./
COPY frontend/src ./src
COPY frontend/public ./public

# Build application
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 3: Production Runner
FROM node:18-alpine AS runner

WORKDIR /app

# Install dumb-init for proper signal handling
RUN apk add --no-cache dumb-init

# Create non-root user
RUN addgroup -S -g node node && \
    adduser -S -G node -h /var/www node

# Copy built application from builder
COPY --from=builder --chown=node:node /app/.next /app/.next
COPY --from=builder --chown=node:node /app/public ./public
COPY --from=builder --chown=node:node /app/package*.json ./

# Switch to non-root user
USER node

# Expose port
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Start application with dumb-init
ENTRYPOINT ["dumb-init", "--", "node", "node_modules/.bin/next", "start"]

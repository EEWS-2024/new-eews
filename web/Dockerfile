# 1. Install dependencies
FROM node:18-alpine AS deps

WORKDIR /app

# Copy only yarn files to cache dependencies
COPY package.json yarn.lock ./

RUN yarn install --frozen-lockfile

# 2. Build the app
FROM node:18-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NODE_ENV=production

COPY .env .env

RUN yarn build

# 3. Production runtime
FROM node:18-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

# Optional: Enable faster startup and smaller image
ENV NEXT_TELEMETRY_DISABLED=1

# Copy necessary files
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/yarn.lock ./yarn.lock
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/next.config.js ./next.config.js
COPY --from=builder /app/.env .env

EXPOSE 3000

CMD ["yarn", "start"]

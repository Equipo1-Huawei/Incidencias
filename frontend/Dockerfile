FROM node:18-alpine AS base

WORKDIR /app

RUN apk add --no-cache iptables iproute2 stress-ng curl

COPY package.json package-lock.json ./
RUN npm ci --production

COPY . .

RUN npm run build

EXPOSE 3000

ENV PORT=3000
ENV NODE_ENV=production

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

CMD ["npm", "start"]

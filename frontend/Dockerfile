FROM node:18-alpine AS base

WORKDIR /app

# Install dependencies required for network tools and chaos testing
RUN apk add --no-cache iptables iproute2 stress-ng

COPY package.json ./
RUN npm install

COPY . .

RUN npm run build

EXPOSE 3000

ENV PORT 3000
ENV NODE_ENV production

CMD ["npm", "start"]

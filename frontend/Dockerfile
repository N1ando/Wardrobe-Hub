FROM node:22-alpine

WORKDIR /app

# For a remote demo (AMD box), pass the public API origin at build time:
#   docker compose build --build-arg VITE_API_BASE=http://<host>:8000 web
# Default targets a local `docker compose up` where :8000 is published.
ARG VITE_API_BASE=http://localhost:8000
ENV VITE_API_BASE=$VITE_API_BASE

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 5173

CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]

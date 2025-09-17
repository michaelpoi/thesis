FROM node:20-alpine
ENV REACT_APP_API_URL="http://127.0.0.1/api"
WORKDIR /app

COPY package*.json ./
RUN npm install
RUN npm install three

COPY . .

RUN npm run build

# Use `serve` to serve the static files
RUN npm install -g serve

EXPOSE 3000

CMD ["serve", "-s", "build", "-l", "3000"]

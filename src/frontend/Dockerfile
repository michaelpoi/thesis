FROM node:20-alpine
ENV REACT_APP_API_URL="http://127.0.0.1/api"
WORKDIR /app
COPY package*.json ./
RUN rm -rf build
RUN npm install
COPY . .
RUN npm run build
VOLUME ["/app/build"]

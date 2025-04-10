FROM node:20-alpine
ENV REACT_APP_API_URL=http://127.0.0.1:8000
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
RUN npm install -g serve
EXPOSE 3000
CMD ["serve", "-s", "build", "-l", "3000"]

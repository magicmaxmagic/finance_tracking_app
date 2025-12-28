FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy app
COPY . .

# Build
RUN npm run build

# Start
EXPOSE 3000
CMD ["npm", "run", "start"]

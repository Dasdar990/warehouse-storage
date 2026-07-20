FROM node:22-alpine

WORKDIR /app

# Copia i file dei pacchetti
COPY package*.json ./

# Installa le dipendenze dentro il container
RUN npm install

# Copia il resto del codice
COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
FROM oven/bun:1-alpine

WORKDIR /app

# Copia i file delle dipendenze (package.json e bun.lock / bun.lockb se presenti)
COPY package*.json bun.lock* ./

# Installa le dipendenze usando Bun
RUN bun install --frozen-lockfile

# Copia il resto del codice dell'applicazione
COPY . .

EXPOSE 3000

# Avvia lo script 'dev' definito nel package.json tramite Bun
CMD ["bun", "run", "dev"]
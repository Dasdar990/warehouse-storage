<template>
  <div class="lottie-style-anim">
    <svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
      <!-- Sfondo del Lettore -->
      <rect
        x="130"
        y="50"
        width="140"
        height="180"
        rx="24"
        class="reader-base"
      />
      <rect
        x="145"
        y="65"
        width="110"
        height="110"
        rx="16"
        class="reader-screen"
      />

      <!-- Simbolo NFC statico -->
      <g class="nfc-symbol">
        <path d="M 190 105 A 15 15 0 0 1 190 135" class="nfc-arc" />
        <path d="M 200 98 A 25 25 0 0 1 200 142" class="nfc-arc" />
        <path d="M 210 91 A 35 35 0 0 1 210 149" class="nfc-arc" />
      </g>

      <!-- UI Successo (Spunta + Cerchio) -->
      <g class="success-ui">
        <circle cx="200" cy="120" r="30" class="success-circle" />
        <path d="M 188 120 l 8 8 l 18 -18" class="success-check" />
      </g>

      <!-- Gruppo MANO + CARTA (Animato insieme) -->
      <g class="hand-and-card">
        <!-- 1. Palmo / Braccio (Sotto la carta) -->
        <path
          d="M 230 320 C 220 270, 240 230, 270 210 C 285 200, 310 210, 320 220 L 350 250 L 320 320 Z"
          fill="#f1c27d"
        />

        <!-- 2. La Carta / Badge -->
        <g class="smart-card">
          <rect
            x="150"
            y="150"
            width="100"
            height="140"
            rx="12"
            class="card-body"
          />
          <rect
            x="175"
            y="160"
            width="50"
            height="8"
            rx="4"
            class="card-detail"
          />
          <circle cx="200" cy="195" r="16" class="card-avatar" />
          <!-- Chip NFC sulla carta -->
          <rect x="165" y="180" width="16" height="12" rx="2" fill="#f59e0b" />
        </g>

        <!-- 3. Pollice (Sopra la carta per simulare la presa) -->
        <path
          d="M 245 225 C 235 210, 220 215, 215 228 C 210 240, 225 250, 240 245 Z"
          fill="#e5b369"
        />
      </g>
    </svg>
  </div>
</template>

<script setup lang="ts">
// Animazione 100% CSS puro - Versione lenta
</script>

<style scoped>
.lottie-style-anim {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
}

svg {
  width: 100%;
  height: auto;
  overflow: visible;
}

/* --- STILI STATICI --- */
.reader-base {
  fill: #1e293b;
}
.reader-screen {
  fill: #0f172a;
}

.nfc-arc {
  fill: none;
  stroke: #475569;
  stroke-width: 4;
  stroke-linecap: round;
}

/* Stili Carta */
.card-body {
  fill: #ffffff;
  stroke: #e2e8f0;
  stroke-width: 2;
  filter: drop-shadow(0 10px 15px rgba(0, 0, 0, 0.15));
}
.card-detail {
  fill: #cbd5e1;
}
.card-avatar {
  fill: #94a3b8;
}

/* --- ANIMAZIONI CSS (Durata ciclo aumentata a 7s) --- */

/* 1. Movimento elastico e lento di Mano + Carta */
.hand-and-card {
  transform-origin: 200px 220px;
  animation: tapMotion 7s cubic-bezier(0.34, 1.56, 0.64, 1) infinite;
}

@keyframes tapMotion {
  0%,
  10% {
    transform: translateY(130px) rotate(12deg);
    opacity: 0;
  }
  25% {
    transform: translateY(0px) rotate(0deg);
    opacity: 1;
  }
  30%,
  65% {
    transform: translateY(-10px) scale(0.98);
  }
  75%,
  100% {
    transform: translateY(130px) rotate(-10deg);
    opacity: 0;
  }
}

/* 2. Scomparsa morbida dell'icona NFC */
.nfc-symbol {
  animation: fadeNfc 7s ease-in-out infinite;
}

@keyframes fadeNfc {
  0%,
  20% {
    opacity: 1;
  }
  28%,
  68% {
    opacity: 0;
    transform: scale(0.8);
  }
  75%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

/* 3. Disegno progressivo del cerchio verde */
.success-circle {
  fill: none;
  stroke: #22c55e;
  stroke-width: 4;
  stroke-dasharray: 190;
  stroke-dashoffset: 190;
  transform-origin: 200px 120px;
  transform: rotate(-90deg);
  animation: drawCircle 7s ease-in-out infinite;
}

@keyframes drawCircle {
  0%,
  30% {
    stroke-dashoffset: 190;
  }
  42%,
  68% {
    stroke-dashoffset: 0;
    opacity: 1;
  }
  75%,
  100% {
    stroke-dashoffset: 190;
    opacity: 0;
  }
}

/* 4. Disegno lento della spunta verde */
.success-check {
  fill: none;
  stroke: #22c55e;
  stroke-width: 5;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-dasharray: 40;
  stroke-dashoffset: 40;
  animation: drawCheck 7s ease-out infinite;
}

@keyframes drawCheck {
  0%,
  42% {
    stroke-dashoffset: 40;
  }
  50%,
  68% {
    stroke-dashoffset: 0;
    opacity: 1;
  }
  75%,
  100% {
    stroke-dashoffset: 40;
    opacity: 0;
  }
}

/* Chi ha richiesto meno movimento nel sistema: ferma le animazioni
   sul fotogramma "a riposo" (carta visibile, simbolo NFC statico). */
@media (prefers-reduced-motion: reduce) {
  .hand-and-card,
  .nfc-symbol,
  .success-circle,
  .success-check {
    animation: none;
  }
  .hand-and-card {
    transform: translateY(0) rotate(0deg);
    opacity: 1;
  }
}
</style>

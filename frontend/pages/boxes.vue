<template>
  <div class="flex flex-col gap-4">
    <section>
      <h2 class="mb-1 text-[1.15rem]">📦 Boxes</h2>
      <p class="m-0 text-sm text-muted">
        Containers for generic items with no room for their own label (e.g.
        loose cables). Rename a box, move it to a different shelf, print its
        label, or see what's inside.
      </p>
    </section>

    <section class="rounded-card border border-edge bg-surface p-4 shadow-card">
      <AdminBoxManager />
    </section>
  </div>
</template>

<script setup lang="ts"></script>

<template>
  <div class="flex flex-col gap-5">
    <section>
      <h2 class="mb-1 text-[1.15rem]">Categories</h2>
      <p class="m-0 text-sm text-muted">Manage the categories available when creating a new item.</p>
    </section>

    <section class="rounded-card border border-edge bg-surface p-5 shadow-card">
      <AdminCategoryManager />
    </section>
  </div>
</template>

<script setup lang="ts"></script>

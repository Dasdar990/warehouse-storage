<template>
  <div class="flex flex-col gap-4">
    <section class="card flex flex-wrap items-center justify-between gap-3 py-3">
      <div>
        <h2 class="text-[1.05rem] font-semibold">Activity Log</h2>
        <p class="mt-1 text-sm text-muted">
          Full history of deposits, withdrawals, and moves across the warehouse.
        </p>
      </div>
    </section>

    <ActivityLog />
  </div>
</template>

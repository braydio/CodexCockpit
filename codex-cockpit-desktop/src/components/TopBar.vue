<template>
  <header class="topbar">
    <div class="left">
      <div class="title">CodexCockpit</div>
      <div class="small muted mono">api={{ api }}</div>
    </div>
  </header>
</template>

<script setup lang="ts">
defineProps<{
  api: string;
}>();
</script>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  background: var(--panel);
}

.title {
  font-weight: 900;
}

.small {
  font-size: 12px;
}

.muted {
  color: var(--muted);
}
</style>


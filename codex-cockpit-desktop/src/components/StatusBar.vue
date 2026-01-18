<template>
  <footer class="statusbar">
    <div class="left">
      <span class="pill mono" :class="statusKind">{{ statusText }}</span>
      <span class="mono muted small" v-if="detail">{{ detail }}</span>
    </div>

    <div class="right mono small muted">
      <span v-if="sessionId">session={{ sessionId }}</span>
      <span v-else>no session</span>
    </div>
  </footer>
</template>

<script setup lang="ts">
defineProps<{
  statusText: string;
  statusKind: "neutral" | "good" | "warn" | "bad";
  detail: string;
  sessionId: string;
}>();
</script>

<style scoped>
.statusbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 12px;
}
</style>

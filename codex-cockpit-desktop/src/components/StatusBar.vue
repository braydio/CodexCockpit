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
  border-top: 1px solid var(--border);
  background: var(--panel);
}

.pill {
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: rgba(255,255,255,0.03);
}

.pill.good {
  border-color: rgba(158, 206, 106, 0.45);
  color: var(--good);
}

.pill.bad {
  border-color: rgba(247, 118, 142, 0.45);
  color: var(--bad);
}

.small {
  font-size: 12px;
}

.muted {
  color: var(--muted);
}
</style>


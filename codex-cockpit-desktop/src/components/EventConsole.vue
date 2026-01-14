<template>
  <section class="consoleWrap">
    <div class="consoleHeader">
      <div class="left">
        <div class="title">Event Console</div>
        <div class="small muted">Streaming SSE events from backend</div>
      </div>

      <div class="right">
        <label class="toggle">
          <input type="checkbox" v-model="autoscroll" />
          <span>Autoscroll</span>
        </label>

        <select class="select mono" v-model="filter">
          <option value="all">all</option>
          <option value="system">system</option>
          <option value="plan">plan</option>
          <option value="thought">thought</option>
          <option value="tool">tool</option>
          <option value="diff">diff</option>
          <option value="status">status</option>
          <option value="final">final</option>
          <option value="cancelled">cancelled</option>
          <option value="error">error</option>
        </select>
      </div>
    </div>

    <div class="console" ref="consoleEl">
      <div v-if="filtered.length === 0" class="empty">
        No events yet. Create a session and run.
      </div>

      <div
        v-for="(e, i) in filtered"
        :key="i"
        class="event"
        :class="e.type"
      >
        <div class="meta">
          <span class="badge" :class="e.type">{{ e.type }}</span>
          <span class="ts mono">{{ formatTs(e.ts) }}</span>
        </div>

        <div class="content mono">
          <span v-if="e.type === 'thought'">{{ e.content }}</span>
          <span v-else>{{ e.content }}</span>
        </div>

        <details v-if="e.meta" class="details">
          <summary class="mono muted">meta</summary>
          <pre class="codeblock mono">{{ pretty(e.meta) }}</pre>
        </details>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onUpdated, ref, watch } from "vue";
import type { CodexEvent } from "@/types/codex";

const props = defineProps<{
  events: CodexEvent[];
  autoscroll: boolean;
}>();

const emit = defineEmits<{
  (e: "update:autoscroll", v: boolean): void;
}>();

const consoleEl = ref<HTMLDivElement | null>(null);
const filter = ref<string>("all");

const autoscroll = computed({
  get: () => props.autoscroll,
  set: (v: boolean) => emit("update:autoscroll", v),
});

const filtered = computed(() => {
  if (filter.value === "all") return props.events;
  return props.events.filter(e => e.type === filter.value);
});

function pretty(obj: any) {
  try { return JSON.stringify(obj, null, 2); }
  catch { return String(obj); }
}

function formatTs(ts?: number) {
  if (!ts) return "—";
  const d = new Date(ts);
  return d.toLocaleTimeString();
}

async function scrollToBottom() {
  await nextTick();
  if (!consoleEl.value) return;
  consoleEl.value.scrollTop = consoleEl.value.scrollHeight;
}

watch(
  () => props.events.length,
  async () => {
    if (props.autoscroll) await scrollToBottom();
  }
);

onUpdated(async () => {
  if (props.autoscroll) await scrollToBottom();
});
</script>

<style scoped>
.consoleWrap {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
}

.consoleHeader {
  padding: 12px 12px;
  border-bottom: 1px solid var(--border);
  background: rgba(255,255,255,0.02);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.title {
  font-weight: 800;
}

.right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: 12px;
  user-select: none;
}

.console {
  flex: 1;
  overflow: auto;
  padding: 12px;
  font-family: var(--mono);
}

.empty {
  color: var(--muted);
  padding: 14px;
  border: 1px dashed var(--border);
  border-radius: 12px;
}

.event {
  padding: 10px 10px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: rgba(255,255,255,0.02);
  margin-bottom: 10px;
}

.event.error {
  border-color: rgba(247, 118, 142, 0.45);
  background: rgba(247, 118, 142, 0.08);
}
.event.final {
  border-color: rgba(158, 206, 106, 0.35);
  background: rgba(158, 206, 106, 0.06);
}

.meta {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 8px;
}

.badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  color: var(--muted);
  background: rgba(255,255,255,0.03);
}

.badge.error {
  color: var(--bad);
  border-color: rgba(247, 118, 142, 0.45);
}

.badge.final {
  color: var(--good);
  border-color: rgba(158, 206, 106, 0.45);
}

.ts {
  color: var(--muted);
  font-size: 12px;
}

.content {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 12px;
  line-height: 1.5;
}

.details summary {
  cursor: pointer;
  margin-top: 8px;
}
.muted { color: var(--muted); }
</style>

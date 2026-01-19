<template>
  <section class="consoleWrap panel secondary">
    <div class="consoleHeader panel-header">
      <div class="left">
        <div class="title">Event Console</div>
        <div class="small muted">Streaming SSE events from backend</div>
      </div>

      <div class="controls toolbar compact">
        <div class="toolbar-group">
          <label class="toggle compact">
            <input type="checkbox" v-model="autoscroll" />
            <span>Autoscroll</span>
          </label>
        </div>

        <div class="toolbar-group">
          <label class="toggle compact">
            <input type="checkbox" v-model="compactView" />
            <span>Compact view</span>
          </label>
        </div>

        <div class="toolbar-group">
          <input
            class="input compact mono"
            v-model="contentFilter"
            type="text"
            placeholder="Filter content"
            aria-label="Filter event content"
          />
        </div>

        <div class="toolbar-group">
          <select class="select compact mono" v-model="typeFilter">
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
    </div>

    <div class="console panel-body" ref="consoleEl">
      <div v-if="filtered.length === 0" class="empty">
        No events yet. Create a session and run.
      </div>

      <div
        v-for="(e, i) in filtered"
        :key="eventKey(e, i)"
        class="event"
        :class="e.type"
      >
        <div class="meta" :class="{ compact: compactView }">
          <span class="badge" :class="e.type">{{ e.type }}</span>
          <span v-if="!compactView" class="ts mono">{{ formatTs(e.ts) }}</span>
        </div>

        <div class="content mono" :class="{ compact: compactView }">
          <span>{{ displayContent(e, i) }}</span>
        </div>

        <div v-if="shouldShowExpand(e)" class="content-toggle">
          <button
            class="btn ghost compact"
            type="button"
            @click="toggleExpanded(eventKey(e, i))"
          >
            {{ isExpanded(eventKey(e, i)) ? "Collapse" : "Expand" }}
          </button>
        </div>

        <details v-if="e.meta && !compactView" class="details">
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
const typeFilter = ref<string>("all");
const contentFilter = ref<string>("");
const compactView = ref(false);
const expandedKeys = ref<Set<string>>(new Set());
const maxCompactLines = 6;

const autoscroll = computed({
  get: () => props.autoscroll,
  set: (v: boolean) => emit("update:autoscroll", v),
});

const filtered = computed(() => {
  const filterValue = typeFilter.value;
  const query = contentFilter.value.trim().toLowerCase();
  return props.events.filter((event) => {
    if (filterValue !== "all" && event.type !== filterValue) return false;
    if (!query) return true;
    return matchesContentFilter(event.content, query);
  });
});

/**
 * Build a stable key for each event row to track expanded state.
 */
function eventKey(event: CodexEvent, index: number) {
  return `${event.ts ?? "no-ts"}-${event.type}-${index}`;
}

/**
 * Render metadata objects as readable JSON.
 */
function pretty(obj: any) {
  try {
    return JSON.stringify(obj, null, 2);
  } catch {
    return String(obj);
  }
}

/**
 * Normalize event content to a string and return split lines.
 */
function contentLines(content: unknown) {
  return String(content ?? "").split("\n");
}

/**
 * Return display-friendly text for the event content.
 */
function displayContent(event: CodexEvent, index: number) {
  if (!compactView.value) return String(event.content ?? "");
  const lines = contentLines(event.content);
  if (lines.length <= maxCompactLines || isExpanded(eventKey(event, index))) {
    return lines.join("\n");
  }
  // Keep the first chunk of lines to preserve context in compact view.
  return lines.slice(0, maxCompactLines).join("\n");
}

/**
 * Decide whether to show the expand/collapse control.
 */
function shouldShowExpand(event: CodexEvent) {
  if (!compactView.value) return false;
  return contentLines(event.content).length > maxCompactLines;
}

/**
 * Toggle expanded state for a specific event key.
 */
function toggleExpanded(key: string) {
  const next = new Set(expandedKeys.value);
  if (next.has(key)) {
    next.delete(key);
  } else {
    next.add(key);
  }
  expandedKeys.value = next;
}

/**
 * Check whether the event content should be expanded.
 */
function isExpanded(key: string) {
  return expandedKeys.value.has(key);
}

/**
 * Match a content string against the current filter value.
 */
function matchesContentFilter(content: unknown, query: string) {
  return String(content ?? "").toLowerCase().includes(query);
}

/**
 * Format a timestamp for display in the console.
 */
function formatTs(ts?: number) {
  if (!ts) return "—";
  const d = new Date(ts);
  return d.toLocaleTimeString();
}

/**
 * Scroll to the bottom of the console once DOM updates settle.
 */
async function scrollToBottom() {
  await nextTick();
  if (!consoleEl.value) return;
  consoleEl.value.scrollTop = consoleEl.value.scrollHeight;
}

watch(
  () => props.events.length,
  async () => {
    if (props.autoscroll) await scrollToBottom();
  },
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
  overflow: hidden;
}

.consoleHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.title {
  font-weight: 800;
}

.controls {
  justify-content: flex-end;
}

.console {
  flex: 1;
  overflow: auto;
  font-family: var(--font-mono);
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
  background: rgba(255, 255, 255, 0.02);
  margin-bottom: 10px;
}

.event.plan {
  border-color: rgba(125, 207, 255, 0.35);
  background: rgba(125, 207, 255, 0.08);
}

.event.tool {
  border-color: rgba(122, 162, 247, 0.35);
  background: rgba(122, 162, 247, 0.08);
}

.event.thought {
  border-color: rgba(148, 163, 184, 0.4);
  background: rgba(148, 163, 184, 0.06);
}

.event.diff {
  border-color: rgba(158, 206, 106, 0.3);
  background: rgba(158, 206, 106, 0.05);
}

.event.status {
  border-color: rgba(224, 175, 104, 0.35);
  background: rgba(224, 175, 104, 0.08);
}

.event.cancelled {
  border-color: rgba(148, 163, 184, 0.3);
  background: rgba(148, 163, 184, 0.05);
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

.meta.compact {
  margin-bottom: 4px;
}

.badge {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid var(--border);
  color: var(--muted);
  background: rgba(255, 255, 255, 0.03);
}

.badge.plan,
.badge.tool,
.badge.diff,
.badge.status,
.badge.cancelled,
.badge.thought {
  color: var(--text);
}

.badge.plan {
  border-color: rgba(125, 207, 255, 0.4);
  color: var(--info);
}

.badge.tool {
  border-color: rgba(122, 162, 247, 0.4);
  color: var(--accent);
}

.badge.diff {
  border-color: rgba(158, 206, 106, 0.4);
  color: var(--good);
}

.badge.status {
  border-color: rgba(224, 175, 104, 0.4);
  color: var(--warn);
}

.badge.cancelled {
  border-color: rgba(148, 163, 184, 0.35);
  color: var(--muted);
}

.badge.thought {
  border-color: rgba(148, 163, 184, 0.35);
  color: var(--muted);
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

.content-toggle {
  margin-top: 6px;
}

.details summary {
  cursor: pointer;
  margin-top: 8px;
}
</style>

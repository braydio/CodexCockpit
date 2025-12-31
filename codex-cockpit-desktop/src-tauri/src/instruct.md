Got it. Here’s **B** as **full files (no snippets)** for a clean, multi-pane **Vue 3 + TypeScript cockpit UI**:

* Sidebar: model selection, workspace, goal, session controls
* Main pane: live streamed event console (SSE)
* Top bar + status bar
* Typed events + composable session manager
* No external UI libraries (CSS Grid layout)
* Uses your existing API:

  * `POST /sessions/`
  * `POST /sessions/{id}/run`
  * `GET  /sessions/{id}/events` (SSE)
  * `GET  /models`

Below is a complete file set. Create/replace these files inside your Tauri-Vue project.

---

## File tree

```
src/
  App.vue
  main.ts
  style.css
  lib/
    api.ts
  types/
    codex.ts
  composables/
    useCockpitSession.ts
  components/
    TopBar.vue
    CockpitSidebar.vue
    EventConsole.vue
    StatusBar.vue
.env
src-tauri/
  tauri.conf.json
```

---

## `src/main.ts`

```ts
import { createApp } from "vue";
import App from "./App.vue";
import "./style.css";

createApp(App).mount("#app");
```

---

## `src/style.css`

```css
:root {
  --bg: #0b0e14;
  --panel: #111523;
  --panel-2: #0f1320;
  --border: #2a3142;
  --text: #e6e6eb;
  --muted: #aab0c0;
  --accent: #7aa2f7;
  --good: #9ece6a;
  --warn: #e0af68;
  --bad: #f7768e;
  --mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
  --sans: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji";
}

* { box-sizing: border-box; }

html, body {
  height: 100%;
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: var(--sans);
}

button, input, select, textarea {
  font-family: inherit;
}

a {
  color: var(--accent);
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

kbd {
  font-family: var(--mono);
  font-size: 0.9em;
  padding: 2px 6px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: rgba(255,255,255,0.03);
}

.btn {
  background: #1a2032;
  color: var(--text);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 10px 12px;
  cursor: pointer;
  transition: transform 0.03s ease, background 0.15s ease;
}

.btn:hover { background: #1e2740; }
.btn:active { transform: translateY(1px); }
.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn.primary {
  border-color: rgba(122, 162, 247, 0.45);
  background: rgba(122, 162, 247, 0.10);
}
.btn.primary:hover {
  background: rgba(122, 162, 247, 0.16);
}

.btn.danger {
  border-color: rgba(247, 118, 142, 0.45);
  background: rgba(247, 118, 142, 0.10);
}
.btn.danger:hover {
  background: rgba(247, 118, 142, 0.16);
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.label {
  color: var(--muted);
  font-size: 12px;
}

.input, .select, .textarea {
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  color: var(--text);
  border-radius: 10px;
  padding: 10px 10px;
  outline: none;
}

.textarea {
  min-height: 110px;
  resize: vertical;
  font-family: var(--sans);
}

.mono {
  font-family: var(--mono);
}

.hr {
  height: 1px;
  background: var(--border);
  margin: 14px 0;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(255,255,255,0.03);
  color: var(--muted);
  font-size: 12px;
}

.pill .dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--muted);
}

.pill.good .dot { background: var(--good); }
.pill.warn .dot { background: var(--warn); }
.pill.bad .dot { background: var(--bad); }

.small {
  color: var(--muted);
  font-size: 12px;
}

.codeblock {
  font-family: var(--mono);
  font-size: 12px;
  line-height: 1.45;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 10px;
  white-space: pre-wrap;
  word-break: break-word;
}
```

---

## `src/lib/api.ts`

```ts
import type { ModelInfo, CreateSessionResponse, ModelsResponse } from "@/types/codex";

export function apiBase(): string {
  return (import.meta as any).env?.VITE_API_BASE || "http://127.0.0.1:8787";
}

export async function fetchModels(): Promise<ModelInfo[]> {
  const res = await fetch(`${apiBase()}/models/`, { method: "GET" });
  if (!res.ok) {
    throw new Error(`Failed to fetch models: ${res.status} ${res.statusText}`);
  }
  const data = (await res.json()) as ModelsResponse;
  return data.models ?? [];
}

export async function createSession(payload: {
  goal: string;
  model: string;
  workspace: string;
}): Promise<CreateSessionResponse> {
  const res = await fetch(`${apiBase()}/sessions/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Create session failed: ${res.status} ${res.statusText} ${text}`);
  }

  return (await res.json()) as CreateSessionResponse;
}

export async function startRun(sessionId: string): Promise<void> {
  const res = await fetch(`${apiBase()}/sessions/${sessionId}/run`, {
    method: "POST",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Start run failed: ${res.status} ${res.statusText} ${text}`);
  }
}
```

---

## `src/types/codex.ts`

```ts
export type CodexEventType =
  | "system"
  | "plan"
  | "thought"
  | "tool"
  | "diff"
  | "final"
  | "error";

export type CodexEvent = {
  type: CodexEventType;
  content: string;
  meta?: Record<string, any>;
  ts?: number; // client-side timestamp
};

export type ModelInfo = {
  name: string;
  type?: "local" | "openai" | string;
  context?: number;
  tools?: boolean;
};

export type ModelsResponse = {
  models: ModelInfo[];
};

export type CreateSessionResponse = {
  session_id: string;
  goal: string;
  model: string;
  status: string;
};
```

---

## `src/composables/useCockpitSession.ts`

```ts
import { computed, onBeforeUnmount, ref } from "vue";
import type { CodexEvent, ModelInfo } from "@/types/codex";
import { apiBase, createSession, fetchModels, startRun } from "@/lib/api";

type SessionStatus =
  | "idle"
  | "loading-models"
  | "ready"
  | "creating-session"
  | "session-created"
  | "running"
  | "completed"
  | "error";

export function useCockpitSession() {
  const status = ref<SessionStatus>("idle");
  const statusDetail = ref<string>("");

  const models = ref<ModelInfo[]>([]);
  const selectedModel = ref<string>("");

  const workspace = ref<string>(".");
  const goal = ref<string>("");

  const sessionId = ref<string>("");
  const events = ref<CodexEvent[]>([]);
  const autoscroll = ref<boolean>(true);

  let source: EventSource | null = null;

  const api = computed(() => apiBase());

  const hasSession = computed(() => Boolean(sessionId.value));
  const canRun = computed(() => hasSession.value && (status.value === "session-created" || status.value === "ready" || status.value === "completed"));

  function pushEvent(e: CodexEvent) {
    events.value.push({ ...e, ts: Date.now() });
  }

  function clearEvents() {
    events.value = [];
  }

  function closeStream() {
    if (source) {
      source.close();
      source = null;
    }
  }

  async function loadModels() {
    status.value = "loading-models";
    statusDetail.value = "Fetching model registry…";
    try {
      const list = await fetchModels();
      models.value = list;

      if (!selectedModel.value) {
        const preferCodex = list.find(m => (m.name || "").toLowerCase().includes("codex"));
        selectedModel.value = preferCodex?.name || list[0]?.name || "codex-default";
      }

      status.value = "ready";
      statusDetail.value = "";
    } catch (err: any) {
      status.value = "error";
      statusDetail.value = err?.message || String(err);
      pushEvent({ type: "error", content: `Model fetch failed: ${statusDetail.value}` });
    }
  }

  async function newSession() {
    if (!goal.value.trim()) {
      pushEvent({ type: "system", content: "Add a goal before creating a session." });
      return;
    }

    status.value = "creating-session";
    statusDetail.value = "Creating session…";
    closeStream();

    try {
      const res = await createSession({
        goal: goal.value,
        model: selectedModel.value,
        workspace: workspace.value || ".",
      });

      sessionId.value = res.session_id;
      status.value = "session-created";
      statusDetail.value = "";

      pushEvent({ type: "system", content: `Session created: ${res.session_id}` });
      pushEvent({ type: "system", content: `Model: ${res.model}` });
    } catch (err: any) {
      status.value = "error";
      statusDetail.value = err?.message || String(err);
      pushEvent({ type: "error", content: `Create session failed: ${statusDetail.value}` });
    }
  }

  async function run() {
    if (!sessionId.value) {
      pushEvent({ type: "system", content: "Create a session first." });
      return;
    }

    status.value = "running";
    statusDetail.value = "Starting run…";
    closeStream();

    // 1) Start execution (POST)
    try {
      await startRun(sessionId.value);
    } catch (err: any) {
      status.value = "error";
      statusDetail.value = err?.message || String(err);
      pushEvent({ type: "error", content: `Run start failed: ${statusDetail.value}` });
      return;
    }

    // 2) Attach SSE (GET)
    statusDetail.value = "Streaming events…";

    const eventsUrl = `${api.value}/sessions/${sessionId.value}/events`;
    pushEvent({ type: "system", content: `Connecting SSE: ${eventsUrl}` });

    source = new EventSource(eventsUrl);

    source.onmessage = (msg) => {
      try {
        const evt = JSON.parse(msg.data) as CodexEvent;
        pushEvent(evt);

        if (evt.type === "final") {
          status.value = "completed";
          statusDetail.value = "Completed";
          closeStream();
        }

        if (evt.type === "error") {
          status.value = "error";
          statusDetail.value = "Error";
          closeStream();
        }
      } catch (e: any) {
        pushEvent({ type: "error", content: `Bad event payload: ${String(e)}` });
      }
    };

    source.onerror = () => {
      pushEvent({ type: "error", content: "SSE connection error (stream closed or backend unreachable)." });
      status.value = "error";
      statusDetail.value = "SSE error";
      closeStream();
    };
  }

  function stopLocal() {
    pushEvent({ type: "system", content: "Stopped (local UI). Stream closed." });
    status.value = "ready";
    statusDetail.value = "";
    closeStream();
  }

  const statusPill = computed(() => {
    const s = status.value;
    if (s === "running") return { kind: "warn" as const, text: "Running" };
    if (s === "completed") return { kind: "good" as const, text: "Completed" };
    if (s === "error") return { kind: "bad" as const, text: "Error" };
    if (s === "session-created") return { kind: "good" as const, text: "Session Ready" };
    if (s === "creating-session" || s === "loading-models") return { kind: "warn" as const, text: "Working…" };
    return { kind: "good" as const, text: "Ready" };
  });

  onBeforeUnmount(() => closeStream());

  return {
    api,
    status,
    statusDetail,
    statusPill,

    models,
    selectedModel,

    workspace,
    goal,

    sessionId,
    hasSession,
    canRun,

    events,
    autoscroll,

    loadModels,
    newSession,
    run,
    stopLocal,
    clearEvents,
  };
}
```

---

## `src/components/TopBar.vue`

```vue
<template>
  <header class="topbar">
    <div class="left">
      <div class="brand">
        <span class="logo"></span>
        <div class="titleWrap">
          <div class="title">Codex Cockpit</div>
          <div class="subtitle">Session-driven AI control plane</div>
        </div>
      </div>
    </div>

    <div class="right">
      <div class="hint mono">
        <span class="muted">API:</span> {{ api }}
      </div>
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
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 14px;
  background: var(--panel);
  border-bottom: 1px solid var(--border);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo {
  width: 14px;
  height: 14px;
  border-radius: 4px;
  background: var(--accent);
  display: inline-block;
  box-shadow: 0 0 0 3px rgba(122, 162, 247, 0.15);
}

.titleWrap {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.title {
  font-weight: 700;
  letter-spacing: 0.2px;
}

.subtitle {
  color: var(--muted);
  font-size: 12px;
}

.hint {
  color: var(--text);
  font-size: 12px;
}

.muted {
  color: var(--muted);
}
</style>
```

---

## `src/components/StatusBar.vue`

```vue
<template>
  <footer class="statusbar">
    <div class="left">
      <span class="pill" :class="pillClass">
        <span class="dot"></span>
        {{ statusText }}
      </span>
      <span class="detail" v-if="detail">{{ detail }}</span>
    </div>

    <div class="right">
      <span class="mono small">Session:</span>
      <span class="mono small value">{{ sessionId || "—" }}</span>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  statusText: string;
  statusKind: "good" | "warn" | "bad";
  detail: string;
  sessionId: string;
}>();

const pillClass = computed(() => {
  if (props.statusKind === "bad") return "bad";
  if (props.statusKind === "warn") return "warn";
  return "good";
});
</script>

<style scoped>
.statusbar {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 6px 12px;
  border-top: 1px solid var(--border);
  background: var(--panel);
}

.left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.detail {
  color: var(--muted);
  font-size: 12px;
}

.right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.value {
  color: var(--text);
}
</style>
```

---

## `src/components/CockpitSidebar.vue`

```vue
<template>
  <aside class="sidebar">
    <div class="section">
      <div class="sectionTitle">Session</div>

      <div class="field">
        <div class="label">Model</div>
        <select class="select" v-model="selectedModel" :disabled="busyModels">
          <option v-for="m in models" :key="m.name" :value="m.name">
            {{ m.name }}{{ m.type ? ` (${m.type})` : "" }}
          </option>
        </select>
        <div class="small mono muted" v-if="selectedModelInfo">
          ctx={{ selectedModelInfo.context ?? "?" }} • tools={{ selectedModelInfo.tools ?? false }}
        </div>
      </div>

      <div class="field">
        <div class="label">Workspace</div>
        <input class="input mono" v-model="workspace" placeholder="." />
        <div class="small muted">Path is interpreted by the backend.</div>
      </div>

      <div class="field">
        <div class="label">Goal</div>
        <textarea class="textarea" v-model="goal" placeholder="What should the agent do?" />
      </div>

      <div class="row">
        <button class="btn" @click="loadModels" :disabled="busyModels">Reload Models</button>
        <button class="btn primary" @click="newSession" :disabled="busyCreate">
          Create Session
        </button>
      </div>

      <div class="hr"></div>

      <div class="field">
        <div class="label">Session ID</div>
        <div class="codeblock mono">{{ sessionId || "—" }}</div>
      </div>

      <div class="row">
        <button class="btn primary" @click="run" :disabled="!canRun || busyRun">
          Run
        </button>
        <button class="btn danger" @click="stopLocal" :disabled="!busyRun">
          Stop (Local)
        </button>
      </div>

      <div class="row">
        <button class="btn" @click="clearEvents">Clear Console</button>
      </div>

      <div class="small muted">
        Stop(Local) only closes the stream. Add a backend stop endpoint later if desired.
      </div>
    </div>

    <div class="section">
      <div class="sectionTitle">Notes</div>
      <div class="small muted">
        Next steps on the roadmap:
        <div class="mono" style="margin-top:8px;">
          B) UI layout ✅<br/>
          C) Diff + workspace viewer<br/>
          D) Model routing ✅<br/>
          E) Tauri desktop ✅
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { ModelInfo } from "@/types/codex";

const props = defineProps<{
  models: ModelInfo[];
  selectedModel: string;
  workspace: string;
  goal: string;
  sessionId: string;
  canRun: boolean;
  status: string;
}>();

const emit = defineEmits<{
  (e: "update:selectedModel", v: string): void;
  (e: "update:workspace", v: string): void;
  (e: "update:goal", v: string): void;
  (e: "loadModels"): void;
  (e: "newSession"): void;
  (e: "run"): void;
  (e: "stopLocal"): void;
  (e: "clearEvents"): void;
}>();

const selectedModel = computed({
  get: () => props.selectedModel,
  set: (v: string) => emit("update:selectedModel", v),
});

const workspace = computed({
  get: () => props.workspace,
  set: (v: string) => emit("update:workspace", v),
});

const goal = computed({
  get: () => props.goal,
  set: (v: string) => emit("update:goal", v),
});

const busyModels = computed(() => props.status === "loading-models");
const busyCreate = computed(() => props.status === "creating-session");
const busyRun = computed(() => props.status === "running");

const selectedModelInfo = computed(() => props.models.find(m => m.name === props.selectedModel) || null);

function loadModels() { emit("loadModels"); }
function newSession() { emit("newSession"); }
function run() { emit("run"); }
function stopLocal() { emit("stopLocal"); }
function clearEvents() { emit("clearEvents"); }
</script>

<style scoped>
.sidebar {
  height: 100%;
  background: var(--panel);
  border-right: 1px solid var(--border);
  padding: 14px;
  overflow: auto;
}

.section {
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 12px;
  margin-bottom: 12px;
}

.sectionTitle {
  font-weight: 700;
  margin-bottom: 10px;
}

.row {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.row .btn {
  flex: 1;
}

.muted { color: var(--muted); }
</style>
```

---

## `src/components/EventConsole.vue`

```vue
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
          <option value="final">final</option>
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
```

---

## `src/App.vue`

```vue
<template>
  <div class="app">
    <TopBar :api="api" />

    <main class="main">
      <CockpitSidebar
        :models="models"
        v-model:selectedModel="selectedModel"
        v-model:workspace="workspace"
        v-model:goal="goal"
        :sessionId="sessionId"
        :canRun="canRun"
        :status="status"
        @loadModels="loadModels"
        @newSession="newSession"
        @run="run"
        @stopLocal="stopLocal"
        @clearEvents="clearEvents"
      />

      <div class="content">
        <EventConsole
          :events="events"
          v-model:autoscroll="autoscroll"
        />
      </div>
    </main>

    <StatusBar
      :statusText="statusPill.text"
      :statusKind="statusPill.kind"
      :detail="statusDetail"
      :sessionId="sessionId"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import TopBar from "@/components/TopBar.vue";
import CockpitSidebar from "@/components/CockpitSidebar.vue";
import EventConsole from "@/components/EventConsole.vue";
import StatusBar from "@/components/StatusBar.vue";
import { useCockpitSession } from "@/composables/useCockpitSession";

const {
  api,
  status,
  statusDetail,
  statusPill,

  models,
  selectedModel,
  workspace,
  goal,

  sessionId,
  canRun,

  events,
  autoscroll,

  loadModels,
  newSession,
  run,
  stopLocal,
  clearEvents,
} = useCockpitSession();

onMounted(async () => {
  await loadModels();
});
</script>

<style scoped>
.app {
  height: 100vh;
  display: grid;
  grid-template-rows: 56px 1fr 36px;
}

.main {
  display: grid;
  grid-template-columns: 340px 1fr;
  gap: 12px;
  padding: 12px;
  overflow: hidden;
}

.content {
  height: 100%;
  overflow: hidden;
}
</style>
```

---

## `.env` (project root)

```env
VITE_API_BASE=http://127.0.0.1:8787
```

---

## `src-tauri/tauri.conf.json`

This includes the “always run with the workaround” environment so you don’t have to prefix commands.

**Replace your file with this** (or merge carefully if you already customized bundle metadata):

```json
{
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devPath": "http://localhost:1420",
    "distDir": "../dist"
  },
  "package": {
    "productName": "Codex Cockpit",
    "version": "0.1.0"
  },
  "tauri": {
    "environment": {
      "WEBKIT_DISABLE_DMABUF_RENDERER": "1",
      "WEBKIT_DISABLE_COMPOSITING_MODE": "1",
      "WINIT_UNIX_BACKEND": "x11"
    },
    "windows": [
      {
        "label": "main",
        "title": "Codex Cockpit",
        "width": 1200,
        "height": 800,
        "resizable": true,
        "fullscreen": false
      }
    ],
    "bundle": {
      "active": true,
      "identifier": "com.brayden.codexcockpit",
      "targets": "all",
      "icon": [
        "icons/32x32.png",
        "icons/128x128.png",
        "icons/128x128@2x.png",
        "icons/icon.icns",
        "icons/icon.ico"
      ]
    },
    "security": {
      "csp": null
    }
  }
}
```

---

# Run it

From the Tauri project:

```bash
npm install
npm run tauri dev
```

Make sure your backend is running too (in another terminal):

```bash
cd backend
./run.sh
```

---

# Next: C (Diff + Workspace)

B is now in place (real cockpit layout + typed session stream). The next step **C** is where we add:

* workspace file tree
* diff viewer (Monaco or lightweight textual diff)
* “open file”, “apply patch”, “save” operations (via backend or Tauri Rust commands)

When you’re ready, say **C** and I’ll generate the **full file set** for that too.


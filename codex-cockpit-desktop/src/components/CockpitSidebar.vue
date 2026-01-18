<template>
  <aside class="sidebar panel">
    <div class="section card">
      <div class="sectionTitle">Session</div>

      <div class="field">
        <div class="label">Model</div>
        <select class="select" v-model="selectedModel" :disabled="busyModels">
          <option v-for="m in models" :key="m.name" :value="m.name">
            {{ m.name }}{{ m.type ? ` (${m.type})` : "" }}
          </option>
        </select>
        <div class="small mono muted" v-if="selectedModelInfo">
          ctx={{ selectedModelInfo.context ?? "?" }} • tools={{
            selectedModelInfo.tools ?? false
          }}
        </div>
      </div>

      <div class="field">
        <div class="label">Workspace</div>
        <input class="input mono" v-model="workspace" placeholder="." />
        <div class="small muted">Path is interpreted by the backend.</div>
      </div>

      <div class="field">
        <div class="label">Goal</div>
        <textarea
          class="textarea"
          v-model="goal"
          placeholder="What should the agent do?"
        />
      </div>

      <div class="row align-center">
        <button class="btn" @click="loadModels" :disabled="busyModels">
          Reload Models
        </button>
        <button class="btn primary" @click="newSession" :disabled="busyCreate">
          Create Session
        </button>
      </div>

      <div class="hr"></div>

      <div class="field">
        <div class="label">Session ID</div>
        <div class="codeblock mono">{{ sessionId || "—" }}</div>
      </div>

      <div class="row align-center">
        <button class="btn primary" @click="run" :disabled="!canRun || busyRun">
          Run
        </button>
        <button class="btn danger" @click="stopLocal" :disabled="!busyRun">
          Stop (Local)
        </button>
      </div>

      <div class="row align-center">
        <button class="btn" @click="clearEvents">Clear Console</button>
      </div>

      <div class="small muted">
        Stop(Local) only closes the stream. Backend stop is available at `POST
        /sessions/{id}/stop`.
      </div>
    </div>

    <div class="section card">
      <div class="sectionTitle">Notes</div>
      <div class="small muted">
        Next steps on the roadmap:
        <div class="mono" style="margin-top: 8px">
          B) UI layout ✅<br />
          C) Diff + workspace viewer<br />
          D) Model routing ✅<br />
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

const selectedModelInfo = computed(
  () => props.models.find((m) => m.name === props.selectedModel) || null,
);

function loadModels() {
  emit("loadModels");
}
function newSession() {
  emit("newSession");
}
function run() {
  emit("run");
}
function stopLocal() {
  emit("stopLocal");
}
function clearEvents() {
  emit("clearEvents");
}
</script>

<style scoped>
.sidebar {
  height: 100%;
  padding: 14px;
  overflow: auto;
}

.row .btn {
  flex: 1;
}

.section.card {
  margin-bottom: 12px;
}
</style>

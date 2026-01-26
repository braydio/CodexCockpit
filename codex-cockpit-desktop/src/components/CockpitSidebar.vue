<template>
  <aside class="sidebar panel">
    <!-- SESSION PANEL -->
    <div class="section card panel">
      <div class="panel-header">
        <div class="sectionTitleRow">
          <div>
            <div class="sectionTitle">1. Session setup</div>
            <div class="panelSubtext">
              Choose endpoint, fetch models, then set the goal before creating a session.
            </div>
          </div>
          <div class="pillLabel">required</div>
        </div>
      </div>

      <div class="panel-body columnGap">
        <div class="field cluster">
          <div class="labelRow">
            <div class="label">Workspace</div>
            <div class="hint">Interpreted by backend</div>
          </div>
          <input class="input mono" v-model="workspace" placeholder="." />
        </div>

        <div class="field cluster">
          <div class="labelRow">
            <div class="label">Endpoint</div>
            <div class="hint">Pick provider, then fetch models</div>
          </div>
          <div class="row tight">
            <label class="radio pillRadio">
              <input type="radio" value="default" v-model="endpointMode" />
              <span>Default (OpenAI)</span>
            </label>
            <label class="radio pillRadio">
              <input type="radio" value="custom" v-model="endpointMode" />
              <span>Custom (Ollama)</span>
            </label>
          </div>
          <div class="endpointPicker" ref="endpointPicker" @focusout="onEndpointFocusOut">
            <input
              ref="endpointInput"
              class="input mono"
              :value="endpointInputValue"
              :disabled="endpointMode === 'default'"
              :placeholder="endpointPlaceholder"
              @input="onEndpointInput"
            />
            <button
              class="btn iconButton"
              type="button"
              :disabled="endpointMode === 'default' || !savedEndpoints.length"
              @click="toggleEndpointDropdown"
            >
              ↓
            </button>
            <div
              v-if="endpointMode === 'custom' && endpointDropdownOpen"
              class="endpointDropdown"
            >
              <button
                v-for="endpoint in savedEndpoints"
                :key="endpoint"
                type="button"
                class="dropdownItem mono"
                @click="chooseSavedEndpoint(endpoint)"
              >
                {{ endpoint }}
              </button>
              <div v-if="!savedEndpoints.length" class="dropdownEmpty small muted">
                No saved endpoints yet.
              </div>
            </div>
          </div>
          <div class="inlineActions" v-if="endpointMode === 'custom' && customEndpoint">
            <div class="hint mono">using: {{ effectiveEndpoint || "—" }}</div>
            <div class="actionButtons">
              <button
                v-if="!isCustomSaved"
                class="btn ghost"
                type="button"
                @click="saveCurrentEndpoint"
              >
                Save endpoint
              </button>
              <button
                v-else
                class="btn ghost"
                type="button"
                @click="removeSelectedEndpoint"
              >
                Remove saved
              </button>
            </div>
          </div>
          <div class="inlineActions" v-else>
            <div class="hint mono">default: {{ defaultEndpoint || "—" }}</div>
          </div>

          <div class="row">
            <button
              v-if="endpointMode === 'custom'"
              class="btn wide"
              :class="{ attention: highlightFetchModels }"
              @click="loadOllamaModels(true)"
              :disabled="ollamaLoading"
            >
              Fetch Ollama models
            </button>
            <div v-else class="hint">OpenAI models are prefetched for the default endpoint.</div>
          </div>

          <div class="small mono muted" v-if="ollamaStatus">
            {{ ollamaStatus }}
          </div>
          <div class="codeblock mono" v-if="ollamaModels.length">
            {{ ollamaModels.join("\n") }}
          </div>
        </div>

        <div class="field cluster">
          <div class="labelRow">
            <div class="label">Model</div>
            <button class="btn ghost smallBtn" @click="loadModels" :disabled="busyModels">
              Refresh models
            </button>
          </div>
          <div class="modelCard">
            <select class="select" v-model="selectedModel" :disabled="busyModels">
              <option v-for="m in models" :key="m.name" :value="m.name">
                {{ m.name }}{{ m.type ? ` (${m.type})` : "" }}
              </option>
            </select>
            <div class="modelMeta" v-if="selectedModelInfo">
              <span class="pillMeta">ctx {{ selectedModelInfo.context ?? "?" }}</span>
              <span class="pillMeta">tools {{ selectedModelInfo.tools ?? false }}</span>
              <span class="pillMeta" v-if="selectedModelInfo.endpoint">
                endpoint {{ selectedModelInfo.endpoint }}
              </span>
            </div>
          </div>
        </div>

        <div class="field cluster">
          <div class="label">Goal</div>
          <textarea
            class="textarea"
            v-model="goal"
            placeholder="What should the agent do?"
          />
        </div>

        <div class="row align-center">
          <button class="btn primary wide" @click="newSession" :disabled="busyCreate">
            Create session
          </button>
        </div>

        <div class="hr stepDivider"></div>

        <div class="field">
          <div class="label">Session ID</div>
          <div class="codeblock mono">{{ sessionId || "—" }}</div>
        </div>
      </div>
    </div>

    <!-- EXECUTION PANEL -->
    <div class="section card panel">
      <div class="panel-header">
        <div class="sectionTitleRow">
          <div>
            <div class="sectionTitle">2. Execution</div>
            <div class="panelSubtext">
              Run the active session, stop the local stream, or clear console output.
            </div>
          </div>
          <div class="pillLabel muted">runtime</div>
        </div>
      </div>

      <div class="panel-body">
        <div class="row align-center">
          <button
            class="btn primary wide"
            :class="{ primary: hasSession }"
            @click="run"
            :disabled="!canRun || busyRun"
          >
            {{ hasSession ? "Run" : "Run (create session first)" }}
          </button>
          <button class="btn ghost danger wide" @click="stopLocal" :disabled="!busyRun">
            Stop stream (local)
          </button>
        </div>

        <div class="small muted runHint" v-if="!hasSession">
          Create a session to enable execution.
        </div>
        <div class="small muted runHint" v-else>
          Execution streams to the console below; Stop only closes the local stream.
        </div>

        <div class="secondaryActions">
          <div class="small muted">Secondary actions</div>
          <div class="row align-center">
            <button class="btn secondary wide" @click="clearEvents">
              Clear console
            </button>
          </div>
        </div>

        <div class="small muted">
          Stop stream only closes the local connection. Backend stop is available at
          <code>POST /sessions/{id}/stop</code> if needed.
        </div>
      </div>
    </div>

    <!-- ABOUT PANEL -->
    <div class="section card panel">
      <div class="panel-header">
        <div class="sectionTitleRow">
          <div>
            <div class="sectionTitle">About / Roadmap</div>
            <div class="panelSubtext">High-level plan with details on demand.</div>
          </div>
          <div class="pillLabel">roadmap</div>
        </div>
      </div>
      <div class="panel-body">
        <div class="roadmapList">
          <details open>
            <summary>Stabilize core cockpit experience</summary>
            <div class="small muted roadmapDetails">
              Solidify session flow, endpoint handling, and error visibility. Improve console UX and
              add resilient reconnect behaviors.
            </div>
          </details>
          <details>
            <summary>Workspace & diffing</summary>
            <div class="small muted roadmapDetails">
              Add richer workspace tree, inline file diffs, and quick actions (open/edit). Aim for a
              minimal diff viewer and comment anchors.
            </div>
          </details>
          <details>
            <summary>Model routing & presets</summary>
            <div class="small muted roadmapDetails">
              Support multiple providers with presets, show capability badges, and allow saving
              routing strategies per project.
            </div>
          </details>
          <details>
            <summary>Desktop polish</summary>
            <div class="small muted roadmapDetails">
              Tighten Tauri shell integration, add native notifications, and streamline packaging for
              macOS/Windows/Linux.
            </div>
          </details>
        </div>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { ModelInfo } from "@/types/codex";

const props = defineProps<{
  models: ModelInfo[];
  selectedModel: string;
  workspace: string;
  goal: string;
  endpointMode: "default" | "custom";
  customEndpoint: string;
  selectedSavedEndpoint: string;
  defaultEndpoint: string;
  effectiveEndpoint: string;
  savedEndpoints: string[];
  ollamaModels: string[];
  ollamaStatus: string;
  ollamaLoading: boolean;
  highlightFetchModels: boolean;
  sessionId: string;
  canRun: boolean;
  status: string;
}>();

const emit = defineEmits<{
  (e: "update:selectedModel", v: string): void;
  (e: "update:workspace", v: string): void;
  (e: "update:goal", v: string): void;
  (e: "update:endpointMode", v: "default" | "custom"): void;
  (e: "update:customEndpoint", v: string): void;
  (e: "update:selectedSavedEndpoint", v: string): void;
  (e: "loadModels"): void;
  (e: "loadOllamaModels", userTriggered?: boolean): void;
  (e: "saveCurrentEndpoint"): void;
  (e: "removeSelectedEndpoint"): void;
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

const endpointMode = computed({
  get: () => props.endpointMode,
  set: (v: "default" | "custom") => emit("update:endpointMode", v),
});

const customEndpoint = computed({
  get: () => props.customEndpoint,
  set: (v: string) => emit("update:customEndpoint", v),
});

const selectedSavedEndpoint = computed({
  get: () => props.selectedSavedEndpoint,
  set: (v: string) => emit("update:selectedSavedEndpoint", v),
});

const defaultEndpoint = computed(() => props.defaultEndpoint);
const isCustomSaved = computed(() => {
  if (!customEndpoint.value) return false;
  return props.savedEndpoints.includes(customEndpoint.value);
});

const endpointDropdownOpen = ref(false);
const endpointPicker = ref<HTMLElement | null>(null);
const endpointInput = ref<HTMLInputElement | null>(null);

const busyModels = computed(() => props.status === "loading-models");
const busyCreate = computed(() => props.status === "creating-session");
const busyRun = computed(() => props.status === "running");
const hasSession = computed(() => Boolean(props.sessionId));

const selectedModelInfo = computed(
  () => props.models.find((m) => m.name === props.selectedModel) || null,
);

const endpointPlaceholder = computed(() =>
  endpointMode.value === "default"
    ? defaultEndpoint.value || "Default endpoint"
    : "Type or pick a saved endpoint",
);

const endpointInputValue = computed(() =>
  endpointMode.value === "default" ? "" : customEndpoint.value,
);

function loadModels() { emit("loadModels"); }
function loadOllamaModels(userTriggered = false) {
  emit("loadOllamaModels", userTriggered);
}
function saveCurrentEndpoint() { emit("saveCurrentEndpoint"); }
function removeSelectedEndpoint() { emit("removeSelectedEndpoint"); }
function newSession() { emit("newSession"); }
function run() { emit("run"); }
function stopLocal() { emit("stopLocal"); }
function clearEvents() { emit("clearEvents"); }

function onEndpointInput(event: Event) {
  const target = event.target as HTMLInputElement;
  if (endpointMode.value !== "custom") {
    endpointMode.value = "custom";
  }
  customEndpoint.value = target.value;
  if (!target.value) {
    selectedSavedEndpoint.value = "";
  }
}

function toggleEndpointDropdown() {
  if (endpointMode.value !== "custom") {
    endpointMode.value = "custom";
  }
  endpointDropdownOpen.value = !endpointDropdownOpen.value;
  if (endpointDropdownOpen.value) {
    endpointInput.value?.focus();
  }
}

function chooseSavedEndpoint(endpoint: string) {
  endpointMode.value = "custom";
  customEndpoint.value = endpoint;
  selectedSavedEndpoint.value = endpoint;
  endpointDropdownOpen.value = false;
}

function onEndpointFocusOut(event: FocusEvent) {
  const next = event.relatedTarget as Node | null;
  if (!endpointPicker.value || (next && endpointPicker.value.contains(next))) {
    return;
  }
  endpointDropdownOpen.value = false;
}
</script>

<style scoped>
.sidebar {
  height: 100%;
  padding: 14px;
  overflow: auto;
}

.section {
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 12px;
  margin-bottom: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.22);
}

.sectionTitle {
  font-weight: 700;
  margin-bottom: 10px;
}

.sectionTitleRow {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.sectionTitle.subsection {
  margin-top: 8px;
  font-size: 13px;
  color: var(--muted);
}

.row {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.radio {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--muted);
  font-size: 12px;
}

.row .btn {
  flex: 1;
}

.section.card {
  margin-bottom: 12px;
}

.stepDivider {
  margin: 16px 0 12px;
}

.runHint {
  margin-top: 6px;
}

.secondaryActions {
  margin-top: 14px;
}

.secondaryActions .btn.secondary {
  opacity: 0.72;
}

.secondaryActions .btn.secondary:hover:not(:disabled) {
  opacity: 0.9;
}

.panelSubtext {
  font-size: 12px;
  color: var(--muted);
}

.columnGap {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.labelRow {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.hint {
  color: var(--muted);
  font-size: 12px;
}

.pillLabel {
  border: 1px solid var(--border);
  padding: 4px 8px;
  border-radius: 999px;
  font-size: 11px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.6px;
}

.row.tight {
  margin-top: 6px;
  gap: 8px;
}

.btn.wide {
  width: 100%;
}

.btn.ghost {
  background: transparent;
  border-color: rgba(255, 255, 255, 0.08);
  color: var(--muted);
}

.btn.ghost:hover:not(:disabled) {
  border-color: rgba(122, 162, 247, 0.45);
  color: var(--text);
}

.btn.smallBtn {
  padding: 6px 10px;
  border-radius: 8px;
}

.section.card {
  margin-bottom: 12px;
}

.stepDivider {
  margin: 16px 0 12px;
}

.endpointPicker {
  position: relative;
  display: flex;
  gap: 8px;
  align-items: center;
}

.endpointPicker .input {
  flex: 1;
  background: rgba(255, 255, 255, 0.04);
}

.iconButton {
  width: 34px;
  padding: 0;
  text-align: center;
  font-weight: 700;
}

.endpointDropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 6px;
  display: grid;
  gap: 4px;
  z-index: 10;
  max-height: 180px;
  overflow-y: auto;
}

.dropdownItem {
  text-align: left;
  padding: 6px 8px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text);
}

.dropdownItem:hover {
  background: rgba(122, 162, 247, 0.12);
  border-color: rgba(122, 162, 247, 0.3);
}

.dropdownEmpty {
  padding: 6px 8px;
}

.inlineActions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 6px;
}

.actionButtons {
  display: flex;
  gap: 8px;
}

.cluster {
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0.00));
}

.pillRadio {
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
}

.pillRadio input {
  accent-color: var(--accent);
}

.modelCard {
  display: flex;
  flex-direction: column;
  gap: 8px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 10px;
}

.modelMeta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pillMeta {
  padding: 4px 8px;
  border-radius: 10px;
  background: rgba(122, 162, 247, 0.12);
  border: 1px solid rgba(122, 162, 247, 0.32);
  color: var(--text);
  font-size: 11px;
}

.btn.attention {
  border-color: rgba(122, 162, 247, 0.7);
  box-shadow:
    0 0 0 2px rgba(122, 162, 247, 0.18),
    0 0 0 8px rgba(122, 162, 247, 0.08);
  animation: attentionPulse 1.4s ease-in-out infinite;
}

@keyframes attentionPulse {
  0% { box-shadow:
    0 0 0 2px rgba(122, 162, 247, 0.14),
    0 0 0 8px rgba(122, 162, 247, 0.05);
  }
  50% { box-shadow:
    0 0 0 2px rgba(122, 162, 247, 0.32),
    0 0 0 10px rgba(122, 162, 247, 0.13);
  }
  100% { box-shadow:
    0 0 0 2px rgba(122, 162, 247, 0.14),
    0 0 0 8px rgba(122, 162, 247, 0.05);
  }
}

.roadmapList details {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 10px 12px;
  margin-bottom: 8px;
}

.roadmapList summary {
  cursor: pointer;
  font-weight: 600;
  color: var(--text);
}

.roadmapDetails {
  margin-top: 6px;
  line-height: 1.5;
}
</style>

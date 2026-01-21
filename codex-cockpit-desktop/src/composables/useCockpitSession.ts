import { computed, ref, watch } from "vue";
import { apiBase } from "@/lib/api";
import type { CodexEvent, ModelInfo } from "@/types/codex";

type CockpitStatus = "idle" | "loading-models" | "creating-session" | "running";

type StatusKind = "neutral" | "good" | "warn" | "bad";

export function useCockpitSession() {
  const api = computed(() => apiBase());

  const status = ref<CockpitStatus>("idle");
  const statusDetail = ref<string>("");

  const models = ref<ModelInfo[]>([]);
  const selectedModel = ref<string>("codex-default");
  const workspace = ref<string>(".");
  const goal = ref<string>("");

  const endpointMode = ref<"default" | "custom">("default");
  const customEndpoint = ref<string>("");
  const savedEndpoints = ref<string[]>([]);
  const selectedSavedEndpoint = ref<string>("");

  const ollamaModels = ref<string[]>([]);
  const ollamaStatus = ref<string>("");
  const ollamaLoading = ref<boolean>(false);
  const highlightFetchModels = ref<boolean>(false);

  const sessionId = ref<string>("");
  const events = ref<CodexEvent[]>([]);
  const autoscroll = ref<boolean>(true);

  let source: EventSource | null = null;
  let streamFinished = false;
  let streamStartedAt = 0;
  let lastEventAt = 0;
  let streamEventCount = 0;

  function pushEvent(e: Omit<CodexEvent, "ts"> & { ts?: number }) {
    events.value.push({ ...e, ts: e.ts ?? Date.now() });
  }

  function closeStream() {
    if (source) {
      source.close();
      source = null;
    }
    streamFinished = false;
    streamStartedAt = 0;
    lastEventAt = 0;
    streamEventCount = 0;
  }

  function streamDiagnosticsLabel() {
    const ageMs = streamStartedAt ? Date.now() - streamStartedAt : 0;
    const idleMs = lastEventAt ? Date.now() - lastEventAt : null;
    const ready = source?.readyState ?? -1;
    const parts = [
      `session=${sessionId.value || "?"}`,
      `readyState=${ready}`,
      `events=${streamEventCount}`,
      `age=${ageMs}ms`,
    ];
    if (idleMs !== null) parts.push(`idle=${idleMs}ms`);
    return parts.join("; ");
  }

  const canRun = computed(() => {
    if (status.value === "running") return false;
    if (!sessionId.value) return false;
    return goal.value.trim().length > 0;
  });

  const statusPill = computed((): { text: string; kind: StatusKind } => {
    if (status.value === "loading-models")
      return { text: "Loading models…", kind: "neutral" };
    if (status.value === "creating-session")
      return { text: "Creating session…", kind: "neutral" };
    if (status.value === "running") return { text: "Running", kind: "good" };
    return { text: "Idle", kind: "neutral" };
  });

  const selectedModelInfo = computed(() => (
    models.value.find(m => m.name === selectedModel.value) || null
  ));

  const defaultEndpoint = computed(() => selectedModelInfo.value?.endpoint || "");

  function normalizeEndpoint(value: string) {
    return value.trim().replace(/\/+$/, "");
  }

  const effectiveEndpoint = computed(() => {
    if (endpointMode.value === "custom") return customEndpoint.value.trim();
    return defaultEndpoint.value || "";
  });

  function loadSavedEndpoints() {
    try {
      const raw = localStorage.getItem("codex-cockpit.endpoints");
      const parsed = raw ? JSON.parse(raw) : [];
      if (Array.isArray(parsed)) {
        savedEndpoints.value = parsed.filter(item => typeof item === "string");
      }
    } catch {
      savedEndpoints.value = [];
    }
  }

  function persistSavedEndpoints() {
    try {
      localStorage.setItem("codex-cockpit.endpoints", JSON.stringify(savedEndpoints.value));
    } catch {
      // ignore storage errors
    }
  }

  function selectSavedEndpoint(value: string) {
    if (!value) return;
    endpointMode.value = "custom";
    customEndpoint.value = value;
    selectedSavedEndpoint.value = value;
  }

  function saveCurrentEndpoint() {
    const candidate = normalizeEndpoint(customEndpoint.value || defaultEndpoint.value || "");
    if (!candidate) {
      ollamaStatus.value = "No endpoint to save.";
      return;
    }
    if (!savedEndpoints.value.includes(candidate)) {
      savedEndpoints.value = [...savedEndpoints.value, candidate];
      persistSavedEndpoints();
    }
    selectedSavedEndpoint.value = candidate;
  }

  function removeSelectedEndpoint() {
    const target = selectedSavedEndpoint.value;
    if (!target) return;
    savedEndpoints.value = savedEndpoints.value.filter(item => item !== target);
    persistSavedEndpoints();
    if (customEndpoint.value === target) {
      customEndpoint.value = "";
    }
    selectedSavedEndpoint.value = "";
  }

  function applyModels(list: ModelInfo[]) {
    models.value = list;
    if (!models.value.find((m) => m.name === selectedModel.value)) {
      selectedModel.value = models.value[0]?.name || "";
    }
  }

  async function loadModels() {
    status.value = "loading-models";
    statusDetail.value = "";

    try {
      if (endpointMode.value === "custom") {
        await loadOllamaModels();
        return;
      }

      const res = await fetch(`${api.value}/models/openai`, { method: "GET" });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(
          `load models failed: ${res.status} ${res.statusText} ${text}`,
        );
      }
      const payload = (await res.json()) as { models?: ModelInfo[] };
      applyModels(payload.models ?? []);
    } catch (e: any) {
      statusDetail.value = e?.message || String(e);
      pushEvent({
        type: "system",
        content: `load models error: ${statusDetail.value}`,
      });
    } finally {
      status.value = "idle";
    }
  }

  async function newSession() {
    closeStream();
    events.value = [];
    statusDetail.value = "";

    status.value = "creating-session";
    try {
      const res = await fetch(`${api.value}/sessions/`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          goal: goal.value,
          model: selectedModel.value,
          workspace: workspace.value || ".",
          endpoint: effectiveEndpoint.value || null,
        }),
      });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(
          `create session failed: ${res.status} ${res.statusText} ${text}`,
        );
      }
      const payload = (await res.json()) as { session_id?: string };
      sessionId.value = payload.session_id ?? "";
      pushEvent({
        type: "system",
        content: `Session created: ${sessionId.value || "unknown"}`,
      });
    } catch (e: any) {
      statusDetail.value = e?.message || String(e);
      pushEvent({
        type: "system",
        content: `create session error: ${statusDetail.value}`,
      });
    } finally {
      status.value = "idle";
    }
  }

  async function run() {
    if (!sessionId.value) return;

    closeStream();
    status.value = "running";
    statusDetail.value = "";

    try {
      const runRes = await fetch(
        `${api.value}/sessions/${encodeURIComponent(sessionId.value)}/run`,
        { method: "POST" },
      );
      if (!runRes.ok) {
        const text = await runRes.text().catch(() => "");
        throw new Error(
          `run failed: ${runRes.status} ${runRes.statusText} ${text}`,
        );
      }

      source = new EventSource(
        `${api.value}/sessions/${encodeURIComponent(sessionId.value)}/events`,
      );
      streamFinished = false;
      streamStartedAt = Date.now();
      streamEventCount = 0;
      lastEventAt = 0;
      source.onopen = () => {
        pushEvent({ type: "system", content: `event stream opened (${streamDiagnosticsLabel()})` });
      };
      source.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data) as CodexEvent;
          streamEventCount += 1;
          lastEventAt = Date.now();
          pushEvent({ ...data, ts: Date.now() });
          if (["final", "error", "cancelled"].includes(data.type)) {
            streamFinished = true;
            closeStream();
            status.value = "idle";
          }
        } catch (e: any) {
          pushEvent({
            type: "system",
            content: `bad event payload: ${e?.message || String(e)}`,
          });
        }
      };
      source.onerror = (err) => {
        const maybeMsg = (err as any)?.message || (err as any)?.data;
        const diag = streamDiagnosticsLabel();
        const detail = maybeMsg ? `${diag}; err=${maybeMsg}` : diag;
        statusDetail.value = `Event stream error (${detail})`;
        if (streamFinished) {
          closeStream();
          return;
        }
        pushEvent({
          type: "system",
          content: statusDetail.value,
        });
        closeStream();
        status.value = "idle";
      };
    } catch (e: any) {
      statusDetail.value = e?.message || String(e);
      pushEvent({ type: "system", content: statusDetail.value });
      status.value = "idle";
    }
  }

  async function stopLocal() {
    closeStream();
    status.value = "idle";
    statusDetail.value = "";

    if (!sessionId.value) return;
    try {
      await fetch(
        `${api.value}/sessions/${encodeURIComponent(sessionId.value)}/stop`,
        { method: "POST" },
      );
    } catch {
      // best-effort
    }
    pushEvent({ type: "system", content: "Stop requested." });
  }

  function clearEvents() {
    events.value = [];
  }

  async function loadOllamaModels(userTriggered = false) {
    if (userTriggered) {
      highlightFetchModels.value = false;
    }

    const endpoint = effectiveEndpoint.value;
    if (!endpoint) {
      ollamaStatus.value = "No endpoint configured for Ollama.";
      applyModels([]);
      return;
    }

    ollamaLoading.value = true;
    ollamaStatus.value = "";
    try {
      const u = new URL(`${api.value}/models/ollama/tags`);
      u.searchParams.set("endpoint", endpoint);
      const res = await fetch(u.toString(), { method: "GET" });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`ollama tags failed: ${res.status} ${res.statusText} ${text}`);
      }
      const payload = (await res.json()) as { models?: string[] };
      ollamaModels.value = payload.models ?? [];
      applyModels(
        ollamaModels.value.map((name) => ({ name, type: "ollama", runtime: "ollama" })),
      );
      ollamaStatus.value = `Found ${ollamaModels.value.length} models.`;
    } catch (e: any) {
      ollamaStatus.value = e?.message || String(e);
    } finally {
      ollamaLoading.value = false;
    }
  }

  loadSavedEndpoints();

  watch(
    () => customEndpoint.value,
    (value) => {
      const normalized = normalizeEndpoint(value);
      if (normalized !== value) {
        customEndpoint.value = normalized;
        return;
      }
      if (normalized && savedEndpoints.value.includes(normalized)) {
        selectedSavedEndpoint.value = normalized;
      }
    },
    { immediate: true }
  );

  watch(
    () => endpointMode.value,
    (mode) => {
      highlightFetchModels.value = mode === "custom" && !models.value.length;
      void loadModels();
    },
  );

  watch(
    () => models.value.length,
    (count) => {
      if (count > 0) {
        highlightFetchModels.value = false;
      }
    },
  );

  return {
    api,
    status,
    statusDetail,
    statusPill,

    models,
    selectedModel,
    workspace,
    goal,
    endpointMode,
    customEndpoint,
    defaultEndpoint,
    effectiveEndpoint,
    savedEndpoints,
    selectedSavedEndpoint,
    ollamaModels,
    ollamaStatus,
    ollamaLoading,
    highlightFetchModels,

    sessionId,
    canRun,

    events,
    autoscroll,

    loadModels,
    newSession,
    run,
    stopLocal,
    clearEvents,
    loadOllamaModels,
    selectSavedEndpoint,
    saveCurrentEndpoint,
    removeSelectedEndpoint,
  };
}

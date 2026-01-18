import { computed, ref } from "vue";
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

  const sessionId = ref<string>("");
  const events = ref<CodexEvent[]>([]);
  const autoscroll = ref<boolean>(true);

  let source: EventSource | null = null;

  function pushEvent(e: Omit<CodexEvent, "ts"> & { ts?: number }) {
    events.value.push({ ...e, ts: e.ts ?? Date.now() });
  }

  function closeStream() {
    if (source) {
      source.close();
      source = null;
    }
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

  async function loadModels() {
    status.value = "loading-models";
    statusDetail.value = "";

    try {
      const res = await fetch(`${api.value}/models/`, { method: "GET" });
      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(
          `load models failed: ${res.status} ${res.statusText} ${text}`,
        );
      }
      const payload = (await res.json()) as { models?: ModelInfo[] };
      models.value = payload.models ?? [];
      if (
        !models.value.find((m) => m.name === selectedModel.value) &&
        models.value.length > 0
      ) {
        selectedModel.value = models.value[0].name;
      }
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
      source.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data) as CodexEvent;
          pushEvent({ ...data, ts: Date.now() });
          if (["final", "error", "cancelled"].includes(data.type)) {
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
      source.onerror = () => {
        pushEvent({ type: "system", content: "event stream error" });
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

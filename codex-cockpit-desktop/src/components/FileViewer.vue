<template>
  <section class="wrap panel secondary">
    <div class="header panel-header">
      <div class="left">
        <div class="title">File Viewer</div>
        <div class="small muted">Click a file in the tree to open</div>
      </div>

      <div class="right">
        <span class="pill mono" v-if="filePath">
          <span class="dot"></span>
          {{ filePath }}
        </span>
        <button class="btn" @click="reload" :disabled="!filePath || loading">
          Reload
        </button>
      </div>
    </div>

    <div class="meta panel-subheader" v-if="fileInfo">
      <div class="mono small">
        <span class="muted">size:</span> {{ fileInfo.size }} bytes
        <span class="muted"> • </span>
        <span class="muted">lines:</span> {{ lineCount }}
        <span class="muted"> • </span>
        <span class="muted">abs:</span> {{ fileInfo.abs_path }}
      </div>
      <div v-if="fileInfo.truncated" class="warn mono small">
        truncated to max_bytes
      </div>
    </div>

    <div class="body panel-body">
      <div v-if="error" class="errorBox mono">{{ error }}</div>
      <div v-else-if="loading" class="loading muted">Loading file…</div>
      <div v-else-if="!filePath" class="emptyState">
        <div class="emptyTitle mono">No file selected</div>
        <div class="small muted">
          Select a file in the workspace tree to preview its contents.
        </div>
      </div>
      <pre v-else class="content mono">{{ fileInfo?.text || placeholder }}</pre>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { WorkspaceFileResponse } from "@/lib/workspaceApi";
import { fetchWorkspaceFile } from "@/lib/workspaceApi";

const props = defineProps<{
  workspace: string;
  filePath: string; // workspace-relative
}>();

const fileInfo = ref<WorkspaceFileResponse | null>(null);
const loading = ref(false);
const error = ref("");

const placeholder = "No file selected.";

/**
 * Count the number of lines in the file contents for display metadata.
 */
function countLines(text?: string | null): number {
  if (!text) return 0;
  return text.split(/\r?\n/).length;
}

const lineCount = computed(() => countLines(fileInfo.value?.text));

// TODO: Add component tests for empty state and metadata rendering when a UI test harness is available.

async function reload() {
  error.value = "";
  fileInfo.value = null;

  if (!props.filePath) return;

  loading.value = true;
  try {
    const res = await fetchWorkspaceFile({
      root: props.workspace || ".",
      path: props.filePath,
      maxBytes: 512000,
    });
    fileInfo.value = res;
  } catch (e: any) {
    error.value = e?.message || String(e);
  } finally {
    loading.value = false;
  }
}

watch(
  () => [props.workspace, props.filePath],
  async () => {
    await reload();
  },
  { immediate: true },
);
</script>

<style scoped>
.wrap {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.title {
  font-weight: 800;
}

.meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.body {
  flex: 1;
  overflow: auto;
}

.content {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.emptyState {
  border: 1px dashed var(--border);
  border-radius: 12px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  background: rgba(255, 255, 255, 0.02);
}

.emptyTitle {
  font-size: 13px;
  font-weight: 600;
}

.errorBox {
  border: 1px solid rgba(247, 118, 142, 0.4);
  background: rgba(247, 118, 142, 0.08);
  border-radius: 12px;
  padding: 10px;
}

.loading {
  padding: 10px;
}

.warn {
  color: var(--warn);
}
</style>

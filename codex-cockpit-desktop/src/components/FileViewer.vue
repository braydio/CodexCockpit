<template>
  <section class="wrap panel secondary">
    <div class="header panel-header">
      <div class="left">
        <div class="title">File Viewer</div>
        <div class="small muted">Click a file in the tree to open</div>
      </div>

      <div class="right">
        <span class="pill mono file-pill" v-if="filePath" :title="fullPath">
          <span class="dot"></span>
          {{ fileName }}
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
        <span class="path">
          <span class="muted">path:</span>
          <span class="path-value" :title="fullPath">{{ fullPath }}</span>
        </span>
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

const fileName = computed(() => {
  if (!props.filePath) return "";
  const segments = props.filePath.split("/");
  return segments[segments.length - 1] || props.filePath;
});

const fullPath = computed(() => fileInfo.value?.abs_path || props.filePath);

// TODO: Add component tests for empty state, metadata rendering, and path truncation when a UI test harness is available.

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
  flex-wrap: wrap;
}

.title {
  font-weight: 800;
}

.left {
  min-width: 0;
}

.right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: flex-end;
  min-width: 0;
}

.file-pill {
  max-width: min(320px, 100%);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.path {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.path-value {
  max-width: min(360px, 60vw);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
  vertical-align: bottom;
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

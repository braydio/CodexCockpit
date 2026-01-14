<template>
  <section class="wrap">
    <div class="header">
      <div class="left">
        <div class="title">Workspace</div>
        <div class="small muted">Browse server workspace files</div>
      </div>

      <div class="right">
        <button class="btn" @click="reload" :disabled="loading">Refresh</button>
        <select class="select mono" v-model="depth" :disabled="loading">
          <option :value="3">depth 3</option>
          <option :value="4">depth 4</option>
          <option :value="5">depth 5</option>
          <option :value="6">depth 6</option>
          <option :value="8">depth 8</option>
        </select>
      </div>
    </div>

    <div class="body">
      <div v-if="error" class="errorBox">
        <div class="mono">{{ error }}</div>
      </div>

      <div v-if="loading" class="loading muted">Loading tree…</div>

      <div v-if="!loading && tree" class="tree mono">
        <TreeNodeView
          :node="tree"
          :selected="selectedPath"
          @open-file="onOpenFile"
        />
      </div>

      <div v-if="!loading && !tree && !error" class="empty muted">
        No tree loaded yet.
      </div>
    </div>

    <div class="footer mono small">
      <span class="muted">root:</span> {{ serverRoot || "—" }}
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { TreeNode } from "@/lib/workspaceApi";
import { fetchWorkspaceTree } from "@/lib/workspaceApi";

const props = defineProps<{
  workspace: string;
  selectedPath: string;
}>();

const emit = defineEmits<{
  (e: "open-file", path: string): void;
  (e: "tree-loaded", payload: { serverRoot: string }): void;
}>();

const tree = ref<TreeNode | null>(null);
const serverRoot = ref<string>("");
const loading = ref(false);
const error = ref<string>("");

const depth = ref<number>(5);

async function reload() {
  error.value = "";
  loading.value = true;
  tree.value = null;

  try {
    const res = await fetchWorkspaceTree({
      root: props.workspace || ".",
      maxDepth: depth.value,
      maxEntries: 5000,
    });
    tree.value = res.tree;
    serverRoot.value = res.root;
    emit("tree-loaded", { serverRoot: res.root });
  } catch (e: any) {
    error.value = e?.message || String(e);
  } finally {
    loading.value = false;
  }
}

function onOpenFile(path: string) {
  emit("open-file", path);
}

watch(
  () => props.workspace,
  async () => {
    // Auto-refresh tree when workspace root changes
    await reload();
  },
  { immediate: true }
);

// ----- TreeNodeView (internal component) -----
const TreeNodeView = defineComponent({
  name: "TreeNodeView",
  props: {
    node: { type: Object as any, required: true },
    selected: { type: String, required: true },
  },
  emits: ["open-file"],
  setup(p, { emit }) {
    const open = ref(true);

    const isDir = computed(() => (p.node as any).type === "dir");
    const isFile = computed(() => (p.node as any).type === "file");
    const isError = computed(() => (p.node as any).type === "error");

    const nodePath = computed(() => (p.node as any).path || "");
    const nodeName = computed(() => (p.node as any).name || "");
    const children = computed(() => (p.node as any).children || []);

    function toggle() {
      if (isDir.value) open.value = !open.value;
    }

    function openFile() {
      if (isFile.value) emit("open-file", (p.node as any).path);
    }

    const isSelected = computed(() => {
      if (!p.selected) return false;
      return p.selected === nodePath.value;
    });

    return () => {
      // root node
      const depthIndent = (nodePath.value.split("/").filter(Boolean).length) * 12;

      const row = h(
        "div",
        {
          class: ["row", isSelected.value ? "selected" : ""],
          style: { paddingLeft: `${depthIndent}px` },
        },
        [
          isDir.value
            ? h("span", { class: ["icon", "dir"], onClick: toggle }, open.value ? "▾" : "▸")
            : h("span", { class: ["icon", isFile.value ? "file" : "err"] }, isError.value ? "!" : "•"),
          h(
            "span",
            {
              class: ["name", isDir.value ? "dir" : isFile.value ? "file" : "err"],
              onDblclick: isDir.value ? toggle : openFile,
              onClick: isFile.value ? openFile : undefined,
              title: isError.value ? (p.node as any).message : nodePath.value || "",
            },
            nodeName.value
          ),
          isError.value ? h("span", { class: "muted", style: { marginLeft: "8px" } }, (p.node as any).message) : null,
        ]
      );

      const kids =
        isDir.value && open.value
          ? h(
              "div",
              { class: "children" },
              children.value.map((c: any) =>
                h(TreeNodeView, {
                  node: c,
                  selected: p.selected,
                  onOpenFile: (path: string) => emit("open-file", path),
                })
              )
            )
          : null;

      return h("div", { class: "node" }, [row, kids]);
    };
  },
});

import { defineComponent, h } from "vue";
</script>

<style scoped>
.wrap {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 14px;
  overflow: hidden;
}

.header {
  padding: 12px;
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

.body {
  flex: 1;
  overflow: auto;
  padding: 10px;
}

.footer {
  padding: 8px 12px;
  border-top: 1px solid var(--border);
  background: rgba(255,255,255,0.02);
}

.tree {
  user-select: none;
}

.row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border-radius: 10px;
  cursor: default;
}

.row:hover {
  background: rgba(255,255,255,0.03);
}

.row.selected {
  background: rgba(122, 162, 247, 0.14);
  border: 1px solid rgba(122, 162, 247, 0.24);
}

.icon {
  width: 16px;
  display: inline-flex;
  justify-content: center;
  color: var(--muted);
}

.name.file {
  cursor: pointer;
  color: var(--text);
}

.name.dir {
  color: var(--muted);
  cursor: pointer;
}

.name.err {
  color: var(--bad);
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

.empty {
  padding: 10px;
}

.muted {
  color: var(--muted);
}

.small {
  font-size: 12px;
}
</style>

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
        <div class="tabs">
          <button
            class="tab"
            :class="{ active: activeTab === 'console' }"
            @click="activeTab = 'console'"
          >
            Console
          </button>
          <button
            class="tab"
            :class="{ active: activeTab === 'workspace' }"
            @click="activeTab = 'workspace'"
          >
            Workspace
          </button>
        </div>

        <div class="pane">
          <EventConsole
            v-if="activeTab === 'console'"
            :events="events"
            v-model:autoscroll="autoscroll"
          />

          <div v-else class="workspaceGrid">
            <WorkspaceTree
              :workspace="workspace"
              :selectedPath="selectedFile"
              @open-file="(p) => (selectedFile = p)"
              @tree-loaded="onTreeLoaded"
            />
            <FileViewer :workspace="workspace" :filePath="selectedFile" />
          </div>
        </div>
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
import { onMounted, ref } from "vue";

import TopBar from "@/components/TopBar.vue";
import CockpitSidebar from "@/components/CockpitSidebar.vue";
import EventConsole from "@/components/EventConsole.vue";
import StatusBar from "@/components/StatusBar.vue";

import WorkspaceTree from "@/components/WorkspaceTree.vue";
import FileViewer from "@/components/FileViewer.vue";

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

const activeTab = ref<"console" | "workspace">("console");
const selectedFile = ref<string>("");

function onTreeLoaded(_payload: { serverRoot: string }) {
  // placeholder hook; later we can show serverRoot in UI or status bar
}

onMounted(async () => {
  await loadModels();
});
</script>

<style scoped>
.tabs {
  justify-self: start;
}
</style>

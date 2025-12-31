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


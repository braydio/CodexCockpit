<template>
  <header class="topbar">
    <div class="left">
      <div class="title">CodexCockpit</div>
      <div class="small muted mono">api={{ api }}</div>
    </div>

    <div class="right">
      <div class="themeLabel small muted mono">Theme</div>
      <select
        class="select mono themeSelect"
        v-model="theme"
        @change="applyTheme"
      >
        <option value="system">system</option>
        <option value="dark">dark</option>
        <option value="light">light</option>
        <option value="gruvbox">gruvbox</option>
        <option value="dracula">dracula</option>
        <option value="nord">nord</option>
      </select>
    </div>
  </header>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

defineProps<{
  api: string;
}>();

type ThemeMode = "system" | "dark" | "light" | "gruvbox" | "dracula" | "nord";

const theme = ref<ThemeMode>("system");

/**
 * Update the document theme attribute so global styles can respond.
 * Custom themes are stored as explicit data-theme values.
 */
function setRootTheme(mode: ThemeMode) {
  const root = document.documentElement;
  if (mode === "system") {
    root.removeAttribute("data-theme");
    return;
  }
  root.setAttribute("data-theme", mode);
}

/**
 * Store the current theme preference for subsequent sessions.
 */
function persistTheme(mode: ThemeMode) {
  localStorage.setItem("cockpit-theme", mode);
}

/**
 * Apply the selected theme immediately and store the preference.
 */
function applyTheme() {
  setRootTheme(theme.value);
  persistTheme(theme.value);
}

/**
 * Recover the previously saved theme preference, if any.
 */
function restoreTheme(): ThemeMode {
  const saved = localStorage.getItem("cockpit-theme") as ThemeMode | null;
  return saved ?? "system";
}

onMounted(() => {
  theme.value = restoreTheme();
  setRootTheme(theme.value);
});
</script>

<style scoped>
.left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title {
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.right {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.themeSelect {
  width: auto;
  min-width: 120px;
}
</style>

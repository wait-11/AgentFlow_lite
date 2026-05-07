<script setup>
import AppHeader from "./components/AppHeader.vue";
import HistoryPanel from "./components/HistoryPanel.vue";
import OutputPanel from "./components/OutputPanel.vue";
import RunForm from "./components/RunForm.vue";
import ToastMessage from "./components/ToastMessage.vue";
import { useWorkbench } from "./composables/useWorkbench";

const {
  activeRun,
  activeStatus,
  copyResult,
  createRun,
  eventCount,
  fillExample,
  form,
  health,
  isSubmitting,
  loadRuns,
  models,
  refreshActiveRun,
  resultOutput,
  roleActivityCount,
  roleCards,
  selectBasicTools,
  selectRun,
  sortedRuns,
  toastMessage,
  toastVisible,
  toggleTool,
  tools,
} = useWorkbench();
</script>

<template>
  <AppHeader :health="health" />

  <main class="workspace">
    <RunForm
      :form="form"
      :is-submitting="isSubmitting"
      :models="models"
      :tools="tools"
      @create-run="createRun"
      @fill-example="fillExample"
      @select-basic-tools="selectBasicTools"
      @toggle-tool="toggleTool"
    />

    <OutputPanel
      :active-run="activeRun"
      :active-status="activeStatus"
      :event-count="eventCount"
      :result-output="resultOutput"
      :role-activity-count="roleActivityCount"
      :role-cards="roleCards"
      @copy-result="copyResult"
      @refresh-active-run="refreshActiveRun"
    />

    <HistoryPanel :runs="sortedRuns" @refresh-runs="loadRuns" @select-run="selectRun" />
  </main>

  <ToastMessage :message="toastMessage" :visible="toastVisible" />
</template>

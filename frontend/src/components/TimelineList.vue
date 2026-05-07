<script setup>
import { formatTime } from "../utils/formatters";

defineProps({
  eventCount: {
    type: Number,
    required: true,
  },
  events: {
    type: Array,
    default: () => [],
  },
});
</script>

<template>
  <div class="timeline-block">
    <div class="label-row">
      <span>事件流</span>
      <span class="muted">{{ eventCount }} events</span>
    </div>
    <ol class="timeline">
      <li v-if="!events.length" class="empty-state">暂无事件</li>
      <li
        v-for="event in events"
        v-else
        :key="event.event_id"
        class="timeline-item"
        :class="`is-${event.type}`"
      >
        <span class="timeline-marker"></span>
        <div>
          <div class="timeline-title">
            <span class="timeline-type">{{ event.type }}</span>
            <span class="timeline-time">{{ formatTime(event.timestamp) }}</span>
          </div>
          <p class="timeline-message">{{ event.message }}</p>
        </div>
      </li>
    </ol>
  </div>
</template>

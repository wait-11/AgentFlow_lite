<script setup>
defineProps({
  form: {
    type: Object,
    required: true,
  },
  isSubmitting: {
    type: Boolean,
    required: true,
  },
  models: {
    type: Array,
    required: true,
  },
  tools: {
    type: Array,
    required: true,
  },
});

defineEmits(["create-run", "fill-example", "select-basic-tools", "toggle-tool"]);
</script>

<template>
  <section class="run-panel" aria-labelledby="newRunTitle">
    <div class="section-heading">
      <div>
        <p class="eyebrow">New Run</p>
        <h2 id="newRunTitle">创建推理任务</h2>
      </div>
      <button class="ghost-button" type="button" @click="$emit('fill-example')">示例</button>
    </div>

    <form class="run-form" @submit.prevent="$emit('create-run')">
      <label class="field-block" for="queryInput">
        <span>问题</span>
        <textarea
          id="queryInput"
          v-model="form.query"
          name="query"
          rows="7"
          placeholder="输入你要 AgentFlow 解决的问题，例如：杭州最有名的湖叫什么？"
          required
        ></textarea>
      </label>

      <div class="form-grid two-columns">
        <label class="field-block" for="modelSelect">
          <span>主模型</span>
          <select id="modelSelect" v-model="form.model" name="model">
            <option v-if="!models.length" value="dashscope">dashscope</option>
            <option v-for="model in models" :key="model.name" :value="model.name">
              {{ model.name }} - {{ model.provider }}
            </option>
          </select>
        </label>

        <label class="field-block" for="baseUrlInput">
          <span>Base URL</span>
          <input
            id="baseUrlInput"
            v-model="form.baseUrl"
            name="baseUrl"
            type="url"
            placeholder="可选，本地 vLLM 或兼容服务"
          />
        </label>
      </div>

      <div class="tool-section">
        <div class="label-row">
          <span>工具</span>
          <button class="link-button" type="button" @click="$emit('select-basic-tools')">基础配置</button>
        </div>
        <div class="tool-grid" aria-live="polite">
          <div v-if="!tools.length" class="empty-state">工具列表加载中</div>
          <label
            v-for="tool in tools"
            v-else
            :key="tool.name"
            class="tool-card"
            :class="{ 'is-selected': form.selectedTools.has(tool.name) }"
          >
            <input
              type="checkbox"
              :value="tool.name"
              :checked="form.selectedTools.has(tool.name)"
              @change="$emit('toggle-tool', tool.name)"
            />
            <span class="tool-name">{{ tool.display_name }}</span>
            <p class="tool-description">{{ tool.description }}</p>
            <span class="tool-meta">{{ tool.name }} / {{ tool.recommended_engine }}</span>
          </label>
        </div>
      </div>

      <div class="form-grid four-columns">
        <label class="field-block compact" for="maxStepsInput">
          <span>步数</span>
          <input id="maxStepsInput" v-model.number="form.maxSteps" name="maxSteps" type="number" min="1" max="30" />
        </label>

        <label class="field-block compact" for="maxTimeInput">
          <span>超时秒</span>
          <input id="maxTimeInput" v-model.number="form.maxTime" name="maxTime" type="number" min="1" max="3600" />
        </label>

        <label class="field-block compact" for="maxTokensInput">
          <span>Token</span>
          <input
            id="maxTokensInput"
            v-model.number="form.maxTokens"
            name="maxTokens"
            type="number"
            min="256"
            max="32000"
            step="256"
          />
        </label>

        <label class="field-block compact" for="temperatureInput">
          <span>温度</span>
          <input
            id="temperatureInput"
            v-model.number="form.temperature"
            name="temperature"
            type="number"
            min="0"
            max="2"
            step="0.1"
          />
        </label>
      </div>

      <div class="submit-row">
        <label class="toggle-row">
          <input v-model="form.verbose" name="verbose" type="checkbox" />
          <span>Verbose</span>
        </label>
        <button class="primary-button" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? "提交中" : "开始推理" }}
        </button>
      </div>
    </form>
  </section>
</template>

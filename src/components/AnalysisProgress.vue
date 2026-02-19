<template>
  <div class="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden animate-fade-up p-6 sm:p-8">
    <!-- 标题 -->
    <div class="text-center mb-6">
      <div class="w-16 h-16 mx-auto mb-3 rounded-full bg-gradient-to-br from-primary to-primary-light flex items-center justify-center shadow-lg shadow-blue-200">
        <svg class="w-8 h-8 text-white animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      </div>
      <h3 class="text-lg font-bold text-gray-800">正在分析影像</h3>
      <p class="text-sm text-gray-400 mt-1">{{ currentStepText }}</p>
    </div>

    <!-- 进度条 -->
    <div class="relative h-2 bg-gray-100 rounded-full overflow-hidden mb-6">
      <div class="absolute inset-y-0 left-0 bg-gradient-to-r from-primary to-accent rounded-full transition-all duration-500 ease-out"
           :style="{ width: progress + '%' }">
        <div class="absolute inset-0 bg-white/30 animate-shimmer"></div>
      </div>
    </div>

    <!-- 步骤列表 -->
    <div class="space-y-3">
      <div v-for="(step, i) in steps" :key="i"
        class="flex items-center gap-3 transition-all duration-300"
        :class="stepState(i) === 'done' ? 'opacity-60' : stepState(i) === 'active' ? 'opacity-100' : 'opacity-30'"
      >
        <!-- 状态图标 -->
        <div class="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-300"
          :class="{
            'bg-green-100 text-green-600': stepState(i) === 'done',
            'bg-blue-100 text-primary animate-pulse': stepState(i) === 'active',
            'bg-gray-100 text-gray-300': stepState(i) === 'pending',
          }"
        >
          <!-- Done check -->
          <svg v-if="stepState(i) === 'done'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
          </svg>
          <!-- Active spinner -->
          <svg v-else-if="stepState(i) === 'active'" class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <!-- Pending dot -->
          <div v-else class="w-2 h-2 rounded-full bg-gray-300"></div>
        </div>

        <!-- 步骤文本 -->
        <div class="flex-1">
          <p class="text-sm font-medium" :class="stepState(i) === 'active' ? 'text-gray-800' : 'text-gray-500'">
            {{ step.icon }} {{ step.label }}
          </p>
          <p v-if="stepState(i) === 'active' && step.detail" class="text-xs text-gray-400 mt-0.5">{{ step.detail }}</p>
        </div>

        <!-- 耗时 -->
        <span v-if="stepState(i) === 'done' && step.elapsed" class="text-xs text-gray-400 font-mono">
          {{ step.elapsed }}
        </span>
      </div>
    </div>

    <!-- 底部动态文案 -->
    <div class="mt-6 text-center">
      <p class="text-xs text-gray-400 animate-pulse">{{ tipText }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';

const props = defineProps({
  isRunning: { type: Boolean, default: true }
});

const currentStep = ref(0);
const progress = ref(0);
let timer = null;
let startTime = Date.now();

const steps = ref([
  { icon: '📤', label: '读取影像', detail: '正在读取您的影像 …', elapsed: null },
  { icon: '🤖', label: 'AI 读片', detail: '正在进行智能影像判读 …', elapsed: null },
  { icon: '📊', label: '综合评估', detail: '正在分析影像细节 …', elapsed: null },
  { icon: '📝', label: '生成报告', detail: '正在整理诊断报告 …', elapsed: null },
]);

const tips = [
  '🩺 AI 正在像医生一样仔细阅读您的影像 …',
  '🔬 正在分析影像中的每一处细节 …',
  '📋 正在综合分析生成专业报告 …',
  '⏱ 分析大约需要 10-30 秒，请耐心等待 …',
  '📋 分析结果仅供参考，请以医生诊断为准',
  '❤️ 愿您早日康复！',
];

const tipIndex = ref(0);
const tipText = computed(() => tips[tipIndex.value % tips.length]);

const currentStepText = computed(() => {
  if (currentStep.value < steps.value.length) {
    return steps.value[currentStep.value].label + ' …';
  }
  return '即将完成';
});

const stepState = (index) => {
  if (index < currentStep.value) return 'done';
  if (index === currentStep.value) return 'active';
  return 'pending';
};

const formatElapsed = (ms) => {
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
};

const advanceStep = () => {
  if (currentStep.value < steps.value.length - 1) {
    const now = Date.now();
    steps.value[currentStep.value].elapsed = formatElapsed(now - startTime);
    startTime = now;
    currentStep.value++;
  }
};

onMounted(() => {
  startTime = Date.now();

  // 模拟进度推进
  const progressTimer = setInterval(() => {
    if (progress.value < 95) {
      // 非线性进度：开始快，后面慢
      const remaining = 95 - progress.value;
      progress.value += Math.max(remaining * 0.08, 0.5);
    }
  }, 200);

  // 步骤推进
  const stepTimers = [
    setTimeout(() => advanceStep(), 1000),    // Step 1 → 2
    setTimeout(() => advanceStep(), 5000),    // Step 2 → 3
    setTimeout(() => advanceStep(), 15000),   // Step 3 → 4
  ];

  // Tip 轮换
  const tipTimer = setInterval(() => {
    tipIndex.value++;
  }, 2500);

  timer = { progressTimer, stepTimers, tipTimer };
});

// 当分析完成时，快速填满进度条
watch(() => props.isRunning, (running) => {
  if (!running) {
    // 标记所有步骤完成
    const now = Date.now();
    for (let i = currentStep.value; i < steps.value.length; i++) {
      if (!steps.value[i].elapsed) {
        steps.value[i].elapsed = formatElapsed(now - startTime);
        startTime = now;
      }
    }
    currentStep.value = steps.value.length;
    progress.value = 100;
  }
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer.progressTimer);
    clearInterval(timer.tipTimer);
    timer.stepTimers?.forEach(t => clearTimeout(t));
  }
});
</script>

<style scoped>
@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
.animate-shimmer {
  animation: shimmer 1.5s infinite;
}
</style>

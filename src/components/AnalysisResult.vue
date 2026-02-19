<template>
  <div class="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden animate-fade-up-delay">
    <!-- ===== 报告头部 ===== -->
    <div class="bg-gradient-to-r from-primary-dark to-primary px-4 sm:px-6 py-5 text-white">
      <div class="flex justify-between items-start">
        <div>
          <h2 class="text-xl sm:text-2xl font-bold tracking-wide">医学影像诊断报告</h2>
          <p class="text-blue-200 text-sm mt-0.5">XPic-AI 智能辅助分析</p>
        </div>
        <div class="text-right text-sm text-blue-200 space-y-0.5 hidden sm:block">
          <p>编号: <span class="text-white font-mono">{{ result.id }}</span></p>
          <p>时间: <span class="text-white font-mono">{{ formattedDate }}</span></p>
        </div>
      </div>
    </div>

    <div class="p-4 sm:p-6 space-y-5">

      <!-- ===== 基本信息 ===== -->
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div class="bg-gray-50 rounded-lg px-3 py-2">
          <span class="text-gray-400">检查类型</span>
          <p class="font-medium text-gray-700">{{ result.scan_type || '影像分析' }}</p>
        </div>
        <div class="bg-gray-50 rounded-lg px-3 py-2">
          <span class="text-gray-400">分析时间</span>
          <p class="font-medium text-gray-700">{{ formattedDate }}</p>
        </div>
      </div>

      <!-- ===== 诊断结论 ===== -->
      <div class="rounded-xl p-4 sm:p-5"
        :class="isNormal
          ? 'bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200'
          : 'bg-gradient-to-r from-red-50 to-orange-50 border border-red-200'"
      >
        <!-- 顶部：标题 + 置信度 -->
        <div class="flex items-center justify-between mb-3">
          <p class="text-sm font-medium text-gray-500">诊断结论</p>
          <div class="flex items-center gap-2">
            <span class="text-xs text-gray-400">置信度</span>
            <div class="relative w-11 h-11">
              <svg class="w-full h-full -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.9" fill="none" stroke="#e5e7eb" stroke-width="3" />
                <circle cx="18" cy="18" r="15.9" fill="none"
                  :stroke="isNormal ? '#16a34a' : '#dc2626'"
                  stroke-width="3" stroke-linecap="round"
                  :stroke-dasharray="`${pct} 100`"
                  class="transition-all duration-700" />
              </svg>
              <span class="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-gray-700">
                {{ pct }}%
              </span>
            </div>
          </div>
        </div>
        <!-- 诊断内容 -->
        <div class="space-y-2" :class="isNormal ? 'text-success' : 'text-danger'">
          <div class="text-base sm:text-lg font-bold leading-relaxed diagnosis-content"
               v-html="renderedDiagnosis"></div>
        </div>
      </div>

      <!-- ===== 影像所见 ===== -->
      <section>
        <h3 class="text-base font-bold text-gray-800 mb-2 flex items-center gap-1.5">
          <span class="w-1 h-4 rounded-full bg-primary inline-block"></span>
          影像所见
        </h3>
        <div class="text-gray-600 leading-relaxed bg-gray-50 rounded-lg p-4 text-[15px] report-content"
             v-html="renderMd(result.findings || '暂无详细所见')"></div>
      </section>

      <!-- ===== 诊断依据 ===== -->
      <section v-if="result.reasoning">
        <h3 class="text-base font-bold text-gray-800 mb-2 flex items-center gap-1.5">
          <span class="w-1 h-4 rounded-full bg-amber-500 inline-block"></span>
          诊断依据
        </h3>
        <div class="text-gray-600 leading-relaxed rounded-lg p-4 text-[15px] bg-amber-50/60 border-l-4 border-amber-400 report-content"
             v-html="renderMd(result.reasoning)"></div>
      </section>

      <!-- ===== 医学建议 ===== -->
      <section>
        <h3 class="text-base font-bold text-gray-800 mb-2 flex items-center gap-1.5">
          <span class="w-1 h-4 rounded-full bg-accent inline-block"></span>
          医学建议
        </h3>
        <div class="text-gray-600 leading-relaxed rounded-lg p-4 text-[15px] bg-cyan-50/60 border-l-4 border-accent report-content"
             v-html="renderMd(result.recommendation)"></div>
      </section>

      <!-- ===== 完整报告（来自通义千问时展示） ===== -->
      <section v-if="result.full_report">
        <details class="group">
          <summary class="text-sm font-semibold text-gray-500 cursor-pointer hover:text-primary transition">
            📋 查看完整 AI 报告原文
          </summary>
          <div class="mt-2 text-gray-600 leading-relaxed bg-blue-50/50 rounded-lg p-4 text-sm border border-blue-100 report-content"
               v-html="renderMd(result.full_report)"></div>
        </details>
      </section>




    </div>

    <!-- ===== 页脚声明 ===== -->
    <div class="bg-red-50 px-4 sm:px-6 py-3 border-t border-red-100">
      <p class="text-center text-xs text-red-400 font-medium">
        ⚠️ 医学免责声明：本报告由 AI 系统自动生成，仅供科研参考。不可替代专业医生的临床诊断。如有不适请立即就医。
      </p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({ result: { type: Object, required: true } });

const isNormal = computed(() =>
  /正常|Normal|未见明显异常/.test(props.result.diagnosis)
);

const pct = computed(() =>
  (props.result.confidence * 100).toFixed(0)
);

// 简易 Markdown 渲染：**粗体**、换行
const renderMd = (text) => {
  if (!text) return '';
  let s = text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  // 粗体（支持跨行）
  s = s.replace(/\*\*([\s\S]+?)\*\*/g, '<strong>$1</strong>');
  // 换行
  s = s.replace(/\n/g, '<br>');
  return s;
};

const renderedDiagnosis = computed(() => renderMd(props.result.diagnosis || ''));

const formattedDate = computed(() => {
  const ts = props.result.timestamp;
  if (!ts || ts === 'Now') return new Date().toLocaleString('zh-CN');
  return new Date(ts).toLocaleString('zh-CN');
});
</script>

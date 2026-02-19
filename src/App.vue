<template>
  <div class="min-h-screen bg-surface flex flex-col">
    <!-- ===== Header ===== -->
    <header class="bg-white border-b border-gray-100 sticky top-0 z-30">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 sm:h-16 flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <span class="text-2xl">🩻</span>
          <h1 class="text-lg sm:text-xl font-bold text-primary-dark tracking-tight">
            XPic-AI
          </h1>
          <span class="hidden sm:inline text-sm text-gray-400 ml-1">医学影像智能分析</span>
        </div>
        <div class="flex items-center gap-2">
        </div>
      </div>
    </header>

    <!-- ===== Main ===== -->
    <main class="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">



      <!-- ────── Upload View ────── -->
      <!-- ────── Analyzing View (进度动画) ────── -->
      <div v-if="isAnalyzing" class="max-w-xl mx-auto animate-fade-up">
        <AnalysisProgress :isRunning="isAnalyzing" />
      </div>

      <!-- ────── Upload View ────── -->
      <div v-else-if="!analysisResult" class="max-w-2xl mx-auto space-y-6 animate-fade-up">
        <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 sm:p-8">
          <h2 class="text-lg font-bold text-gray-800 mb-1">上传 X 光影像</h2>
          <p class="text-sm text-gray-400 mb-5">
            上传一张或直接拍照，AI 将综合分析 45 种可能病症
          </p>

          <ImageUpload v-model="currentFile" />

          <!-- Analyze Button -->
          <button @click="handleAnalyze"
            :disabled="!currentFile"
            class="mt-6 w-full py-3.5 rounded-xl font-bold text-white shadow-md
                   transition-all duration-200
                   bg-gradient-to-r from-primary to-primary-light
                   hover:shadow-lg hover:brightness-110
                   active:scale-[0.98]
                   disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none
                   flex items-center justify-center gap-2 text-[15px]"
          >
            🔍 开始智能分析
          </button>
        </div>

        <!-- Tips for patients -->
        <div class="bg-blue-50 rounded-xl px-4 py-3 text-sm text-blue-700 space-y-1">
          <p class="font-medium">💡 使用提示</p>
          <ul class="text-xs text-blue-600 space-y-0.5 pl-4 list-disc">
            <li>手机用户可点击「拍照上传」直接拍摄</li>
            <li>建议上传清晰、完整的 X 光片影像</li>
            <li>分析结果仅供参考，请以医生诊断为准</li>
          </ul>
        </div>

        <!-- Error Toast -->
        <div v-if="errorMsg"
          class="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm flex items-start gap-2 animate-fade-up">
          <span class="mt-0.5">⚠️</span>
          <div>
            <p class="font-medium">分析失败</p>
            <p class="text-red-500">{{ errorMsg }}</p>
          </div>
        </div>
      </div>

      <!-- ────── Result View ────── -->
      <div v-else id="report-content" class="grid grid-cols-1 lg:grid-cols-5 gap-6">

        <!-- Left Column: Image (2/5) -->
        <div class="lg:col-span-2 space-y-4 animate-fade-up">
          <div class="bg-gray-900 rounded-2xl overflow-hidden shadow flex items-center justify-center p-3"
               style="min-height: 300px;">
            <img v-if="fileUrl" :src="fileUrl"
                 class="max-h-[520px] max-w-full object-contain rounded-lg" alt="影像" />
          </div>

          <!-- Action Buttons (hidden during print) -->
          <div class="grid grid-cols-2 gap-3 no-print">
            <button @click="resetAnalysis"
              class="py-2.5 rounded-xl text-sm font-semibold border-2 border-primary text-primary
                     hover:bg-blue-50 active:scale-[0.98] transition">
              📷 重新上传
            </button>
            <button @click="downloadReport"
              class="py-2.5 rounded-xl text-sm font-semibold bg-gray-800 text-white
                     hover:bg-gray-900 active:scale-[0.98] transition">
              ⬇ 下载报告
            </button>
          </div>

        </div>

        <!-- Right Column: Report (3/5) -->
        <div class="lg:col-span-3">
          <AnalysisResult :result="analysisResult" />
        </div>
      </div>
    </main>

    <!-- ===== Footer ===== -->
    <footer class="bg-white border-t border-gray-100 py-4 no-print">
      <p class="text-center text-xs text-gray-400">
        &copy; 2026 XPic-AI · 仅供科研与辅助参考，不可作为临床诊断依据
      </p>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import ImageUpload      from './components/ImageUpload.vue';
import AnalysisResult   from './components/AnalysisResult.vue';
import AnalysisProgress from './components/AnalysisProgress.vue';
import { analyzeImage } from './services/aiService';

/* ── State ── */
const currentFile    = ref(null);
const analysisResult = ref(null);
const isAnalyzing    = ref(false);
const errorMsg       = ref('');

const fileUrl = computed(() =>
  currentFile.value ? URL.createObjectURL(currentFile.value) : null
);

/* ── Actions ── */
const handleAnalyze = async () => {
  if (!currentFile.value) return;
  errorMsg.value = '';
  isAnalyzing.value = true;
  try {
    const result = await analyzeImage(currentFile.value);
    analysisResult.value = result;
  } catch (e) {
    errorMsg.value = e.message || '发生未知错误，请稍后重试';
    console.error(e);
  } finally {
    isAnalyzing.value = false;
  }
};

const resetAnalysis = () => {
  currentFile.value    = null;
  analysisResult.value = null;
  errorMsg.value       = '';
};

/* ── 下载 PDF 报告（隐藏表单直接提交，兼容所有移动端浏览器）── */
const downloadReport = () => {
  const r = analysisResult.value;
  if (!r) return;

  const apiBase = import.meta.env.VITE_API_BASE || '';

  // 创建隐藏表单直接提交，浏览器原生处理 PDF 下载
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = `${apiBase}/download-pdf`;
  form.target = '_blank';
  form.style.display = 'none';

  // 将报告 JSON 作为隐藏字段
  const input = document.createElement('input');
  input.type = 'hidden';
  input.name = 'report';
  input.value = JSON.stringify(r);
  form.appendChild(input);

  document.body.appendChild(form);
  form.submit();
  document.body.removeChild(form);
};


</script>

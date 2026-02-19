<template>
  <div class="space-y-4">
    <!-- ===== 拍照/上传按钮组 (Mobile-first) ===== -->
    <div v-if="!modelValue" class="space-y-3">
      <!-- 主要上传区域 -->
      <div
        class="relative rounded-2xl border-2 border-dashed p-6 sm:p-8 text-center cursor-pointer
               transition-all duration-300 select-none"
        :class="[
          isDragging
            ? 'border-primary bg-blue-50/60 scale-[1.01] shadow-lg'
            : 'border-gray-300 bg-white hover:border-primary-light hover:bg-blue-50/30'
        ]"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="handleDrop"
        @click="triggerGallery"
      >
        <div class="py-4 space-y-3">
          <div class="w-14 h-14 mx-auto rounded-full bg-blue-100 flex items-center justify-center">
            <svg class="w-7 h-7 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
          </div>
          <p class="text-base font-semibold text-gray-700">点击或拖拽上传影像</p>
          <p class="text-sm text-gray-400">支持 JPG / PNG 格式</p>
        </div>
      </div>

      <!-- 📸 手机拍照按钮 -->
      <button @click="triggerCamera"
        class="w-full py-3.5 rounded-xl font-bold text-white shadow-md
               bg-gradient-to-r from-emerald-500 to-teal-500
               hover:shadow-lg hover:brightness-110
               active:scale-[0.98] transition-all duration-200
               flex items-center justify-center gap-2 text-[15px]"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
          <circle cx="12" cy="13" r="3" stroke-width="2" />
        </svg>
        📸 拍照上传 X 光片
      </button>
    </div>

    <!-- ===== 预览 ===== -->
    <div v-else class="space-y-3">
      <div class="relative rounded-2xl border-2 border-gray-200 bg-white overflow-hidden group cursor-pointer"
           @click="triggerGallery">
        <img :src="imageUrl" class="max-h-72 w-full object-contain p-2" alt="已上传影像" />
        <div class="absolute inset-0 bg-black/50 flex flex-col items-center justify-center
                    opacity-0 group-hover:opacity-100 transition-opacity gap-2">
          <span class="text-white/80 text-sm">点击重新选择</span>
          <button @click.stop="removeImage"
            class="px-4 py-1.5 rounded-full bg-white/20 text-white text-sm backdrop-blur-sm
                   hover:bg-white/30 transition">
            移除此图片
          </button>
        </div>
      </div>
    </div>

    <!-- Hidden file inputs -->
    <input ref="galleryInput" type="file" class="hidden" accept="image/*" @change="handleFileChange" />
    <input ref="cameraInput" type="file" class="hidden" accept="image/*" capture="environment" @change="handleFileChange" />
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue';

const props = defineProps({ modelValue: File });
const emit  = defineEmits(['update:modelValue']);

const isDragging   = ref(false);
const galleryInput = ref(null);
const cameraInput  = ref(null);
const imageUrl     = ref(null);

watch(() => props.modelValue, (f) => {
  if (imageUrl.value) URL.revokeObjectURL(imageUrl.value);
  imageUrl.value = f ? URL.createObjectURL(f) : null;
}, { immediate: true });

onUnmounted(() => { if (imageUrl.value) URL.revokeObjectURL(imageUrl.value); });

const triggerGallery = () => galleryInput.value.click();
const triggerCamera  = () => cameraInput.value.click();

const handleFile = (file) => {
  if (file?.type.startsWith('image/')) {
    emit('update:modelValue', file);
  } else {
    alert('请上传图片文件（JPG / PNG）');
  }
};

const handleDrop       = (e) => { isDragging.value = false; handleFile(e.dataTransfer.files[0]); };
const handleFileChange = (e) => { handleFile(e.target.files[0]); e.target.value = ''; };
const removeImage      = () => emit('update:modelValue', null);
</script>

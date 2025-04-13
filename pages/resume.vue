<!-- pages/resume.vue -->
<template>
    <div class="container mx-auto p-4">
      <NCard title="Resume" class="mb-4">
        <!-- 使用 Nuxt Content 渲染 resume.md 文件的内容 -->
        <NuxtContent document="/resume" />
      </NCard>
      <div class="text-center mt-8">
        <NButton type="primary" @click="downloadCV">CV herunterladen</NButton>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  function downloadCV() {
    // 假设 cv.pdf 文件放在 static 文件夹中
    window.open('/cv.pdf', '_blank');
  }
  </script>
  
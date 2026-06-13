<template>
  <div v-if="isDir" style="display:inline-flex;vertical-align:middle">
    <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none">
      <path d="M2 6C2 4.89543 2.89543 4 4 4H9L11 7H20C21.1046 7 22 7.89543 22 9V18C22 19.1046 21.1046 20 20 20H4C2.89543 20 2 19.1046 2 18V6Z" fill="#E6A23C"/>
      <path d="M2 9H22V18C22 19.1046 21.1046 20 20 20H4C2.89543 20 2 19.1046 2 18V9Z" fill="#F0C060"/>
    </svg>
  </div>
  <div v-else style="display:inline-flex;align-items:center;justify-content:center;vertical-align:middle;position:relative">
    <!-- 文件主体 -->
    <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none">
      <path d="M6 2C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2H6Z" fill="#fff" :stroke="icon.color" stroke-width="1.5"/>
      <path d="M14 2V8H20" fill="none" :stroke="icon.color" stroke-width="1.5"/>
      <!-- 折角 -->
      <path d="M14 2L20 8H14V2Z" :fill="icon.color" fill-opacity="0.15"/>
    </svg>
    <!-- 扩展名标签 -->
    <span
      :style="{
        position: 'absolute',
        bottom: '1px',
        left: '0',
        right: '0',
        textAlign: 'center',
        fontSize: icon.label.length > 4 ? '6px' : '7px',
        fontWeight: '700',
        color: '#fff',
        background: icon.color,
        borderRadius: '2px',
        padding: '0 2px',
        lineHeight: '12px',
        letterSpacing: '0.5px',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
      }"
    >{{ icon.label }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getFileIcon } from '@/utils/fileIcons'

const props = defineProps<{ name: string; isDir: boolean; size?: number }>()
const icon = computed(() => getFileIcon(props.name, props.isDir))
const size = computed(() => props.size || 20)
</script>

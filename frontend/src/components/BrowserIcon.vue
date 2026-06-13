<template>
  <span class="browser-icon" :style="{ display: 'inline-flex', alignItems: 'center', gap: '6px' }">
    <!-- Chrome -->
    <svg v-if="browser.key === 'chrome'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#fff" stroke="#4285F4" stroke-width="0.5"/>
      <path d="M12 2A10 10 0 0 0 4.5 5.5L9.5 14.3A5 5 0 0 1 12 7h9.8A10 10 0 0 0 12 2Z" fill="#DB4437"/>
      <path d="M4.5 5.5A10 10 0 0 0 2 12h7.5a5 5 0 0 1-.2-2.7L4.5 5.5Z" fill="#F4B400"/>
      <path d="M2 12a10 10 0 0 0 5 8.5l4.8-8.3A5 5 0 0 1 9.5 12H2Z" fill="#0F9D58"/>
      <path d="M7 20.5A10 10 0 0 0 12 22a10 10 0 0 0 9.8-8H14.5a5 5 0 0 1-7.5 6.5Z" fill="#4285F4"/>
      <circle cx="12" cy="12" r="4" fill="#fff"/>
      <circle cx="12" cy="12" r="2.5" fill="#4285F4"/>
    </svg>

    <!-- Firefox -->
    <svg v-else-if="browser.key === 'firefox'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#FF7139"/>
      <path d="M12 2c-1 0-2 .5-2.5 1.5C8 5 8 7 9 8.5c-1-.5-2-1.5-2-3C6 3 7 2 8 1.5c2-1 4 0 5 2 .5 1 .5 2 0 3-.5-1-1.5-1.5-2-1.5 1 1 1 2.5.5 4-1.5 2-4 3-6 2.5 0 1 .5 2 1.5 2.5 1 .5 2 .5 3 0 1-.5 1.5-1 2-2 .5 1.5.5 3-.5 4.5 2-.5 3.5-2 4-4 .5-2 0-4-1-5.5 1.5 0 3 1 3.5 2.5.5 2 0 4-1.5 5 2-1 3-3 3-5 0-3-2-5.5-4.5-6.5C15 4 13.5 3.5 12 2Z" fill="#FF980E"/>
      <path d="M12 2c-1.5 1-2.5 2-3 3.5-.5 1.5 0 3 1 4-1-.5-2-1.5-2-3 0-1.5 1-3 2.5-3.5.5-.2 1-.3 1.5-.3Z" fill="#FFBD4F"/>
      <circle cx="14" cy="10" r="1.5" fill="#fff"/>
      <circle cx="14" cy="10" r="0.8" fill="#333"/>
    </svg>

    <!-- Safari -->
    <svg v-else-if="browser.key === 'safari'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#fff" stroke="#006CFF" stroke-width="0.5"/>
      <circle cx="12" cy="12" r="9" fill="none" stroke="#006CFF" stroke-width="0.3" stroke-dasharray="1 1"/>
      <polygon points="12,3 14,10 21,12 14,14 12,21 10,14 3,12 10,10" fill="#006CFF" opacity="0.8"/>
      <polygon points="12,5 13.5,10.5 18,12 13.5,13.5 12,19 10.5,13.5 6,12 10.5,10.5" fill="#FF3B30"/>
      <polygon points="12,5 13.5,10.5 12,12 10.5,10.5" fill="#006CFF"/>
      <polygon points="12,19 13.5,13.5 12,12 10.5,13.5" fill="#006CFF"/>
    </svg>

    <!-- Edge -->
    <svg v-else-if="browser.key === 'edge'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#0078D7"/>
      <path d="M7 14c0-3 2-6 6-6s5 2 5 4c0 2-1 3-3 3H12c-2 0-3 1-3 2s1 2 3 2c3 0 5-2 5-5 0-4-3-7-7-7-4 0-7 3-7 7 0 0 0 0 0 0Z" fill="#50E6FF"/>
      <path d="M7 14c0-1 .5-2 1.5-2.5C9 11 10.5 10.5 12 10.5c1.5 0 3 .5 4 1.5.5.5 1 1.5 1 2.5" fill="none" stroke="#fff" stroke-width="1"/>
    </svg>

    <!-- Opera -->
    <svg v-else-if="browser.key === 'opera'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#FF1B2D"/>
      <ellipse cx="12" cy="12" rx="5" ry="7" fill="none" stroke="#fff" stroke-width="2"/>
      <circle cx="12" cy="12" r="3" fill="#fff"/>
    </svg>

    <!-- IE -->
    <svg v-else-if="browser.key === 'ie'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#0078D7"/>
      <text x="12" y="17" text-anchor="middle" font-size="16" font-weight="bold" font-family="serif" fill="#fff" font-style="italic">e</text>
    </svg>

    <!-- WeChat -->
    <svg v-else-if="browser.key === 'wechat'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#07C160"/>
      <ellipse cx="10" cy="10" rx="5" ry="4" fill="#fff" opacity="0.9"/>
      <circle cx="8.5" cy="9.5" r="0.7" fill="#07C160"/>
      <circle cx="11.5" cy="9.5" r="0.7" fill="#07C160"/>
      <ellipse cx="14" cy="14" rx="4" ry="3" fill="#fff" opacity="0.9"/>
      <circle cx="13" cy="13.5" r="0.5" fill="#07C160"/>
      <circle cx="15" cy="13.5" r="0.5" fill="#07C160"/>
    </svg>

    <!-- QQ -->
    <svg v-else-if="browser.key === 'qq'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#12B7F5"/>
      <ellipse cx="12" cy="11" rx="5" ry="5.5" fill="#fff" opacity="0.9"/>
      <circle cx="10" cy="10" r="1" fill="#333"/>
      <circle cx="14" cy="10" r="1" fill="#333"/>
      <path d="M10 14 Q12 16 14 14" fill="none" stroke="#333" stroke-width="1" stroke-linecap="round"/>
    </svg>

    <!-- 360 -->
    <svg v-else-if="browser.key === '360'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#1DBF1D"/>
      <text x="12" y="16" text-anchor="middle" font-size="12" font-weight="bold" fill="#fff">360</text>
    </svg>

    <!-- UC -->
    <svg v-else-if="browser.key === 'uc'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#FF6A00"/>
      <text x="12" y="16" text-anchor="middle" font-size="11" font-weight="bold" fill="#fff">UC</text>
    </svg>

    <!-- DingTalk -->
    <svg v-else-if="browser.key === 'dingtalk'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#0089FF"/>
      <path d="M12 5L8 9v3l4-2 4 2V9l-4-4Z" fill="#fff"/>
      <path d="M8 12v4l4 3 4-3v-4l-4 2-4-2Z" fill="#fff" opacity="0.8"/>
    </svg>

    <!-- Quark -->
    <svg v-else-if="browser.key === 'quark'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#6A5ACD"/>
      <text x="12" y="16" text-anchor="middle" font-size="10" font-weight="bold" fill="#fff">Q</text>
    </svg>

    <!-- Samsung -->
    <svg v-else-if="browser.key === 'samsung'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#1428A0"/>
      <text x="12" y="15" text-anchor="middle" font-size="7" font-weight="bold" fill="#fff">S</text>
    </svg>

    <!-- Vivaldi -->
    <svg v-else-if="browser.key === 'vivaldi'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#EF3939"/>
      <path d="M12 4L7 19l5-8 5 8L12 4Z" fill="#fff" opacity="0.9"/>
    </svg>

    <!-- Cheetah -->
    <svg v-else-if="browser.key === 'cheetah'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#27C24C"/>
      <text x="12" y="16" text-anchor="middle" font-size="10" font-weight="bold" fill="#fff">C</text>
    </svg>

    <!-- Sogou -->
    <svg v-else-if="browser.key === 'sogou'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#FF6A00"/>
      <text x="12" y="16" text-anchor="middle" font-size="10" font-weight="bold" fill="#fff">S</text>
    </svg>

    <!-- Yandex -->
    <svg v-else-if="browser.key === 'yandex'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#FF0000"/>
      <text x="12" y="16" text-anchor="middle" font-size="10" font-weight="bold" fill="#fff">Y</text>
    </svg>

    <!-- Douyin -->
    <svg v-else-if="browser.key === 'douyin'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#161823"/>
      <text x="12" y="16" text-anchor="middle" font-size="10" font-weight="bold" fill="#25F4EE">DY</text>
    </svg>

    <!-- Android -->
    <svg v-else-if="browser.key === 'android'" :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#3DDC84"/>
      <rect x="8" y="10" width="8" height="7" rx="1" fill="#fff"/>
      <circle cx="10" cy="13" r="1" fill="#333"/>
      <circle cx="14" cy="13" r="1" fill="#333"/>
      <path d="M8 8L9 6M16 8L15 6" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>
      <path d="M9 10V8h6v2" fill="#fff"/>
    </svg>

    <!-- Unknown / Other - Globe -->
    <svg v-else :width="size" :height="size" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#909399"/>
      <circle cx="12" cy="12" r="7" fill="none" stroke="#fff" stroke-width="1"/>
      <ellipse cx="12" cy="12" rx="3" ry="7" fill="none" stroke="#fff" stroke-width="1"/>
      <line x1="5" y1="12" x2="19" y2="12" stroke="#fff" stroke-width="0.8"/>
      <line x1="12" y1="5" x2="12" y2="19" stroke="#fff" stroke-width="0.8"/>
    </svg>

    <span v-if="showName" :style="{ fontSize: fontSize + 'px', color: '#606266' }">{{ browser.name }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { parseBrowser } from '@/utils/browserIcons'

const props = defineProps<{ 
  userAgent: string
  size?: number
  showName?: boolean
  fontSize?: number
}>()

const browser = computed(() => parseBrowser(props.userAgent || ''))
const size = computed(() => props.size || 20)
const fontSize = computed(() => props.fontSize || 13)
</script>

<style scoped>
.browser-icon {
  display: inline-flex;
  align-items: center;
  vertical-align: middle;
}
</style>

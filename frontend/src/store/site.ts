import { defineStore } from 'pinia'
import { ref } from 'vue'
import { settingsApi } from '@/api'

export const useSiteStore = defineStore('site', () => {
  const settings = ref<Record<string, string>>({})
  const loaded = ref(false)

  async function loadSettings() {
    try {
      const token = localStorage.getItem('token')
      let res: any
      if (token) {
        res = await settingsApi.get()
      } else {
        res = await settingsApi.getPublic()
      }
      settings.value = res || {}
      applySettings()
      loaded.value = true
    } catch {}
  }

  function applySettings() {
    const s = settings.value

    // 页面标题
    if (s.site_name) {
      document.title = s.site_name
    }

    // Favicon
    if (s.site_favicon) {
      let link = document.querySelector("link[rel~='icon']") as HTMLLinkElement
      if (!link) {
        link = document.createElement('link')
        link.rel = 'icon'
        document.head.appendChild(link)
      }
      link.href = s.site_favicon
    }
  }

  function get<K extends string>(key: K, fallback: string = ''): string {
    return settings.value[key] || fallback
  }

  return { settings, loaded, loadSettings, applySettings, get }
})

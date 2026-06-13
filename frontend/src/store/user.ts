import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, usersApi } from '@/api'

export interface MenuItem {
  id: number
  parent_id: number
  name: string
  menu_type: string
  permission_code: string
  path: string
  icon: string
  sort_order: number
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref<any>(null)
  const permissions = ref<string[]>([])
  const menus = ref<MenuItem[]>([])
  const roleCode = ref('guest')

  const isAdmin = computed(() => roleCode.value === 'admin')

  // 只取顶级菜单（type=menu, parent_id=0），按 sort_order 排序
  const sidebarMenus = computed(() => {
    return menus.value
      .filter(m => m.menu_type === 'menu' && m.parent_id === 0)
      .sort((a, b) => a.sort_order - b.sort_order)
  })

  async function login(username: string, password: string) {
    const res: any = await authApi.login(username, password)
    token.value = res.access_token
    localStorage.setItem('token', res.access_token)
  }

  async function fetchUserInfo() {
    try {
      const res: any = await usersApi.getMe()
      userInfo.value = res
      roleCode.value = res.role_code || 'guest'
    } catch {}
  }

  async function fetchPermissions() {
    try {
      const res: any = await authApi.getPermissions()
      permissions.value = res.permissions || []
      menus.value = res.menus || []
      roleCode.value = res.role_code || 'guest'
    } catch {
      permissions.value = []
      menus.value = []
    }
  }

  function hasPermission(code: string): boolean {
    if (isAdmin.value) return true
    return permissions.value.includes(code)
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    permissions.value = []
    menus.value = []
    roleCode.value = 'guest'
    localStorage.removeItem('token')
  }

  return { token, userInfo, permissions, menus, roleCode, isAdmin, sidebarMenus, login, fetchUserInfo, fetchPermissions, hasPermission, logout }
})

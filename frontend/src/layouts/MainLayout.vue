<template>
  <el-container style="height: 100vh">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '220px'" style="transition: width 0.3s">
      <div style="height: 60px; display: flex; align-items: center; justify-content: center; border-bottom: 1px solid #e4e7ed">
        <img v-if="siteStore.get('site_logo') && !isCollapse" :src="siteStore.get('site_logo')" style="width:28px;height:28px;object-fit:contain" @error="($event.target as HTMLImageElement).src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTMgMkg2YTIgMiAwIDAwLTIgMnYxNmEyIDIgMCAwMDIgMmgxMmEyIDIgMCAwMDItMlY4bC01LTV6IiBzdHJva2U9IiM0MDlFRkYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+PHBvbHlsaW5lIHBvaW50cz0iMTMgMiA4IDcgMTQgNyIgc3Ryb2tlPSIjNDA5RUZGIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjxsaW5lIHgxPSI4IiB5MT0iMTMiIHgyPSIxNiIgeTI9IjEzIiBzdHJva2U9IiM0MDlFRkYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+PGxpbmUgeDE9IjgiIHkxPSIxNyIgeDI9IjE2IiB5Mj0iMTciIHN0cm9rZT0iIzQwOUVGRiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48L3N2Zz4='" />
        <img v-else-if="!isCollapse" src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTMgMkg2YTIgMiAwIDAwLTIgMnYxNmEyIDIgMCAwMDIgMmgxMmEyIDIgMCAwMDItMlY4bC01LTV6IiBzdHJva2U9IiM0MDlFRkYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+PHBvbHlsaW5lIHBvaW50cz0iMTMgMiA4IDcgMTQgNyIgc3Ryb2tlPSIjNDA5RUZGIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjxsaW5lIHgxPSI4IiB5MT0iMTMiIHgyPSIxNiIgeTI9IjEzIiBzdHJva2U9IiM0MDlFRkYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+PGxpbmUgeDE9IjgiIHkxPSIxNyIgeDI9IjE2IiB5Mj0iMTciIHN0cm9rZT0iIzQwOUVGRiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz48L3N2Zz4=" style="width:28px;height:28px" />
        <span v-if="!isCollapse" style="margin-left: 8px; font-size: 18px; font-weight: 700; color: #409EFF">{{ siteStore.get('site_name', 'UniFile') }}</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        router
        style="border-right: none"
      >
        <el-menu-item
          v-for="item in userStore.sidebarMenus"
          :key="item.id"
          :index="item.path"
        >
          <el-icon><component :is="iconMap[item.icon] || 'Document'" /></el-icon>
          <template #title>{{ item.name }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主体 -->
    <el-container>
      <!-- 顶栏 -->
      <el-header style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e4e7ed; padding: 0 20px">
        <div style="display: flex; align-items: center">
          <el-icon style="cursor: pointer; font-size: 20px" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/" style="margin-left: 16px">
            <el-breadcrumb-item :to="{ path: '/admin/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.meta.title">{{ route.meta.title }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <el-dropdown @command="handleCommand">
          <span style="display: flex; align-items: center; cursor: pointer">
            <el-avatar :size="32" style="background: #409EFF; margin-right: 8px">
              {{ userStore.userInfo?.username?.[0]?.toUpperCase() || 'U' }}
            </el-avatar>
            <span>{{ userStore.userInfo?.username || '用户' }}</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="password">修改密码</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <!-- 内容 -->
      <el-main style="background: #f5f7fa; padding: 16px">
        <router-view />
      </el-main>
    </el-container>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="pwdDialog.visible" title="修改密码" width="400px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="旧密码"><el-input v-model="pwdDialog.old_password" type="password" show-password /></el-form-item>
        <el-form-item label="新密码"><el-input v-model="pwdDialog.new_password" type="password" show-password /></el-form-item>
        <el-form-item label="确认密码"><el-input v-model="pwdDialog.confirm_password" type="password" show-password /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="pwdDialog.loading" @click="changePassword">确认</el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { useSiteStore } from '@/store/site'
import { usersApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Odometer, Box, Share, Setting, User, UserFilled, Menu as MenuIcon, Document, Fold, Expand, Monitor } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const siteStore = useSiteStore()
const isCollapse = ref(false)

// 图标名称映射
const iconMap: Record<string, any> = {
  Odometer,
  Box,
  Share,
  Setting,
  User,
  UserFilled,
  Menu: MenuIcon,
  Document,
  Monitor,
}

const activeMenu = computed(() => {
  if (route.path.startsWith('/admin/files')) return '/admin/storages'
  if (route.path.startsWith('/admin/shares')) return '/admin/shares'
  return route.path
})

function handleCommand(cmd: string) {
  if (cmd === 'logout') {
    userStore.logout()
    router.push('/login')
  } else if (cmd === 'password') {
    pwdDialog.visible = true
    pwdDialog.old_password = ''
    pwdDialog.new_password = ''
    pwdDialog.confirm_password = ''
  }
}

// 修改密码
const pwdDialog = reactive({ visible: false, old_password: '', new_password: '', confirm_password: '', loading: false })

async function changePassword() {
  if (!pwdDialog.old_password || !pwdDialog.new_password) { ElMessage.warning('请填写完整'); return }
  if (pwdDialog.new_password !== pwdDialog.confirm_password) { ElMessage.warning('两次密码不一致'); return }
  if (pwdDialog.new_password.length < 6) { ElMessage.warning('密码至少6位'); return }
  pwdDialog.loading = true
  try {
    await usersApi.changePassword(pwdDialog.old_password, pwdDialog.new_password)
    ElMessage.success('密码已修改，请重新登录')
    pwdDialog.visible = false
    userStore.logout()
    router.push('/login')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '修改失败')
  } finally { pwdDialog.loading = false }
}
</script>

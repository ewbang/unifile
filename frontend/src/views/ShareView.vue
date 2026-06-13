<template>
  <div class="share-page">
    <!-- 密码验证 -->
    <div v-if="needPassword && !verified" class="share-card password-card">
      <div class="lock-icon-wrap">
        <div class="lock-icon-bg">
          <el-icon :size="40" color="#fff"><Lock /></el-icon>
        </div>
      </div>
      <h2 style="margin:20px 0 8px; font-size:22px; color:#303133; text-align:center; font-weight:700">加密分享</h2>
      <p style="color:#909399; font-size:14px; text-align:center; margin:0 0 28px">请输入访问密码查看文件</p>
      <el-input
        v-model="inputPassword"
        placeholder="请输入访问密码"
        type="password"
        show-password
        size="large"
        @keyup.enter="verifyPassword"
        class="password-input"
      >
        <template #prefix><el-icon><Lock /></el-icon></template>
      </el-input>
      <el-button type="primary" size="large" style="width:100%; margin-top:16px; height:44px; font-size:15px; border-radius:8px" :loading="loading" @click="verifyPassword">
        验证并访问
      </el-button>
      <p style="text-align:center; margin:16px 0 0; color:#c0c4cc; font-size:12px">文件: {{ shareInfo?.file_name || '未知文件' }}</p>
    </div>

    <!-- 文件列表 -->
    <div v-else-if="shareData" class="share-main">
      <!-- 顶部卡片 -->
      <div class="share-header-card">
        <div class="share-header">
          <div class="share-header-icon">
            <el-icon :size="28" color="#fff">
              <Folder v-if="shareData.type === 'dir'" />
              <Files v-else-if="shareData.type === 'multi'" />
              <Document v-else />
            </el-icon>
          </div>
          <div class="share-header-info">
            <h2>{{ titleText }}</h2>
            <p>{{ shareData.files?.length || 0 }} 个文件 · {{ shareData.share?.created_at?.slice(0, 10) }}</p>
          </div>
          <!-- 有效期标识 -->
          <div v-if="shareData.share?.expire_at" class="expire-badge" :class="isShareExpired ? 'expire-expired' : isShareUrgent ? 'expire-urgent' : 'expire-normal'">
            <el-icon><Clock /></el-icon>
            <span>{{ expireText }}</span>
          </div>
        </div>
      </div>

      <!-- 过期警告 -->
      <div v-if="shareData.share?.expire_at && isShareExpired" class="expire-block">
        <div class="expire-block-icon">
          <el-icon :size="48" color="#f56c6c"><CircleClose /></el-icon>
        </div>
        <h2 style="margin:16px 0 8px; font-size:20px; color:#f56c6c">分享已过期</h2>
        <p style="color:#909399; font-size:14px; margin:0">此分享链接已过有效期，文件无法访问</p>
      </div>

      <div v-if="!isShareExpired">
      <!-- 面包屑 + 操作栏 -->
      <div class="share-toolbar">
        <div class="breadcrumb-bar">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item v-if="!currentSubpath">
              <span class="breadcrumb-current"><el-icon><HomeFilled /></el-icon></span>
            </el-breadcrumb-item>
            <template v-else>
              <el-breadcrumb-item>
                <a @click.prevent="navigateTo('')"><el-icon><HomeFilled /></el-icon></a>
              </el-breadcrumb-item>
              <el-breadcrumb-item v-for="(crumb, idx) in folderBreadcrumbs" :key="idx">
                <a v-if="idx < folderBreadcrumbs.length - 1" @click.prevent="navigateTo(crumb.path)">{{ crumb.name }}</a>
                <span v-else class="breadcrumb-current">{{ crumb.name }}</span>
              </el-breadcrumb-item>
            </template>
          </el-breadcrumb>
        </div>
        <transition name="el-fade-in">
          <div v-if="selectedFiles.length > 0" class="batch-bar">
            <span>已选 <b>{{ selectedFiles.length }}</b> 项</span>
            <el-button text size="small" @click="clearSelection">取消</el-button>
            <el-button type="primary" size="small" @click="batchDownload">
              <el-icon style="margin-right:4px"><Download /></el-icon>批量下载
            </el-button>
          </div>
        </transition>
      </div>

      <!-- 文件列表 -->
      <div class="share-table-wrap" v-loading="subLoading">
        <table class="file-table">
          <thead>
            <tr>
              <th style="width:40px">
                <el-checkbox v-model="allChecked" :indeterminate="isIndeterminate" @change="onSelectAll" />
              </th>
              <th>名称</th>
              <th style="width:90px">大小</th>
              <th style="width:150px">修改时间</th>
              <th style="width:130px">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in shareData.files" :key="row.path" :class="{ 'row-dir': row.is_dir }">
              <td>
                <el-checkbox v-model="row._checked" :disabled="row.is_dir" @change="(val: boolean) => onRowCheck(row, val)" />
              </td>
              <td>
                <div class="file-name-cell" :class="{ clickable: row.is_dir }" @click="row.is_dir && navigateToFile(row)">
                  <FileIcon :name="row.name" :is-dir="row.is_dir" :size="22" />
                  <span>{{ row.name }}</span>
                </div>
              </td>
              <td class="cell-muted">{{ row.is_dir ? '—' : formatSize(row.size) }}</td>
              <td class="cell-muted">{{ row.last_modified || '—' }}</td>
              <td>
                <div class="action-cell">
                  <el-button v-if="!row.is_dir && isPreviewable(row.name)" type="primary" link size="small" @click="openPreview(row)">预览</el-button>
                  <el-button v-if="!row.is_dir && row.url && shareData.share?.allow_download" type="primary" link size="small" @click="downloadFile(row.url, row.name)">下载</el-button>
                  <span v-if="row.is_dir" class="open-link" @click="navigateToFile(row)">打开</span>
                </div>
              </td>
            </tr>
            <tr v-if="!shareData.files?.length">
              <td colspan="5" class="empty-cell">暂无文件</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 底部信息 -->
      <div class="share-footer">
        <span>由 UniFile 分享</span>
      </div>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="share-card password-card">
      <div class="lock-icon-wrap">
        <div class="lock-icon-bg" style="background: linear-gradient(135deg, #f56c6c 0%, #e63946 100%)">
          <el-icon :size="40" color="#fff"><CircleClose /></el-icon>
        </div>
      </div>
      <h2 style="margin:20px 0 8px; font-size:20px; color:#F56C6C; text-align:center">{{ error }}</h2>
      <p style="text-align:center; color:#909399; font-size:14px">该分享链接可能已失效、过期或被关闭</p>
    </div>

    <!-- 加载中 -->
    <div v-else class="share-card password-card" v-loading="true" style="min-height:200px"></div>

    <!-- 预览弹窗 -->
    <el-dialog v-model="previewVisible" :title="previewFile?.name || '预览'" width="80%" destroy-on-close top="5vh">
      <div style="display:flex; align-items:center; justify-content:center; min-height:300px; background:#000; border-radius:8px; overflow:hidden">
        <img v-if="previewType === 'image'" :src="previewUrl" :alt="previewFile?.name" style="max-width:100%; max-height:80vh; object-fit:contain" />
        <video v-else-if="previewType === 'video'" :src="previewUrl" controls autoplay style="max-width:100%; max-height:80vh" />
        <iframe v-else-if="previewType === 'pdf'" :src="previewUrl" style="width:100%; height:80vh; border:none" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { shareApi } from '@/api'
import { ElMessage } from 'element-plus'
import FileIcon from '@/components/FileIcon.vue'

const route = useRoute()
const loading = ref(false)
const subLoading = ref(false)
const error = ref('')
const needPassword = ref(false)
const verified = ref(false)
const inputPassword = ref('')
const shareInfo = ref<any>(null)
const shareData = ref<any>(null)
const currentSubpath = ref('')
const sharePassword = ref('')
const selectedFiles = ref<any[]>([])
const previewVisible = ref(false)
const previewFile = ref<any>(null)
const previewType = ref<'image' | 'video' | 'pdf' | ''>('')
const previewUrl = computed(() => {
  if (!previewFile.value?.url) return ''
  const url = previewFile.value.url
  if (sharePassword.value && url.includes('/api/shares/access/')) {
    const sep = url.includes('?') ? '&' : '?'
    return `${url}${sep}password=${encodeURIComponent(sharePassword.value)}`
  }
  return url
})

const checkableFiles = computed(() => (shareData.value?.files || []).filter((f: any) => !f.is_dir))
const allChecked = computed(() => checkableFiles.value.length > 0 && checkableFiles.value.every((f: any) => f._checked))
const isIndeterminate = computed(() => {
  const checked = checkableFiles.value.filter((f: any) => f._checked).length
  return checked > 0 && checked < checkableFiles.value.length
})

function onSelectAll(val: boolean) {
  checkableFiles.value.forEach((f: any) => { f._checked = val })
  selectedFiles.value = val ? [...checkableFiles.value] : []
}

const titleText = computed(() => {
  const type = shareData.value?.type
  if (type === 'dir') return '文件夹分享'
  if (type === 'multi') return '多文件分享'
  return '文件分享'
})

const isShareExpired = computed(() => {
  const expireAt = shareData.value?.share?.expire_at
  return expireAt ? new Date(expireAt).getTime() < Date.now() : false
})

const isShareUrgent = computed(() => {
  const expireAt = shareData.value?.share?.expire_at
  if (!expireAt) return false
  const diff = new Date(expireAt).getTime() - Date.now()
  return diff > 0 && diff < 24 * 3600 * 1000
})

const expireText = computed(() => {
  const expireAt = shareData.value?.share?.expire_at
  if (!expireAt) return ''
  const diff = new Date(expireAt).getTime() - Date.now()
  if (diff <= 0) return '已过期'
  const days = Math.floor(diff / 86400000)
  const hours = Math.floor((diff % 86400000) / 3600000)
  const minutes = Math.floor((diff % 3600000) / 60000)
  if (days > 0) return `剩余 ${days} 天 ${hours} 小时`
  if (hours > 0) return `剩余 ${hours} 小时 ${minutes} 分钟`
  return `剩余 ${minutes} 分钟`
})

const folderBreadcrumbs = computed(() => {
  if (!currentSubpath.value) return []
  const type = shareData.value?.type
  if (type === 'dir') {
    const parts = currentSubpath.value.split('/').filter(Boolean)
    return parts.map((name, idx) => ({ name, path: parts.slice(0, idx + 1).join('/') }))
  }
  const parts = currentSubpath.value.split('/').filter(Boolean)
  return parts.map((name, idx) => ({ name, path: '/' + parts.slice(0, idx + 1).join('/') }))
})

function formatSize(bytes: number | null | undefined): string {
  if (!bytes) return '0 B'
  const u = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + u[i]
}

function onRowCheck(row: any, val: boolean) {
  if (val) { if (!selectedFiles.value.some(f => f.path === row.path)) selectedFiles.value.push(row) }
  else { const idx = selectedFiles.value.findIndex(f => f.path === row.path); if (idx >= 0) selectedFiles.value.splice(idx, 1) }
}

function clearSelection() {
  shareData.value?.files?.forEach((f: any) => { f._checked = false })
  selectedFiles.value = []
}

async function loadShare(password?: string, subpath?: string) {
  const code = route.params.code as string
  if (!subpath) loading.value = true; else subLoading.value = true
  error.value = ''
  try {
    const res: any = await shareApi.access(code, password, subpath)
    if (res.type === 'need_password') {
      needPassword.value = true; shareInfo.value = res.share
      localStorage.removeItem(`share_pwd_${code}`)
      verified.value = false
      return
    }
    shareData.value = res; currentSubpath.value = res.subpath || ''; verified.value = true
    if (password) {
      sharePassword.value = password
      localStorage.setItem(`share_pwd_${code}`, password)
    }
  } catch (e: any) {
    const status = e?.response?.status
    // 401密码错误：清除缓存，弹出密码输入框
    if (status === 401 && password) {
      localStorage.removeItem(`share_pwd_${code}`)
      sharePassword.value = ''
      needPassword.value = true
      inputPassword.value = ''
      return
    }
    error.value = e?.response?.data?.detail || '加载失败'
  }
  finally { loading.value = false; subLoading.value = false; selectedFiles.value = [] }
}

async function verifyPassword() { if (!inputPassword.value.trim()) return; await loadShare(inputPassword.value) }

function navigateTo(subpath: string) { loadShare(sharePassword.value || undefined, subpath || undefined) }

function navigateToFile(row: any) {
  if (!row.is_dir) return
  const type = shareData.value?.type
  if (type === 'dir') {
    const shareRoot = shareData.value?.share?.file_path || '/'
    let relativePath = row.path
    if (shareRoot && row.path.startsWith(shareRoot)) relativePath = row.path.slice(shareRoot.length).replace(/^\//, '')
    navigateTo(relativePath)
  } else { navigateTo(row.path) }
}

const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'bmp', 'ico', 'avif']
const videoExts = ['mp4', 'webm', 'ogg', 'mov', 'mkv', 'avi']
const pdfExts = ['pdf']
function isPreviewable(name: string): boolean {
  const ext = name.includes('.') ? name.split('.').pop()!.toLowerCase() : ''
  return [...imageExts, ...videoExts, ...pdfExts].includes(ext)
}
function openPreview(row: any) {
  const ext = row.name.includes('.') ? row.name.split('.').pop()!.toLowerCase() : ''
  if (imageExts.includes(ext)) previewType.value = 'image'
  else if (videoExts.includes(ext)) previewType.value = 'video'
  else if (pdfExts.includes(ext)) previewType.value = 'pdf'
  else return
  previewFile.value = row; previewVisible.value = true
}

async function downloadFile(url: string, name?: string) {
  if (!name) { window.open(url, '_blank'); return }
  let finalUrl = url
  if (sharePassword.value && url.includes('/api/shares/access/')) {
    const sep = url.includes('?') ? '&' : '?'
    finalUrl = `${url}${sep}password=${encodeURIComponent(sharePassword.value)}`
  }
  try {
    const resp = await fetch(finalUrl); const blob = await resp.blob()
    const blobUrl = URL.createObjectURL(blob); const a = document.createElement('a')
    a.href = blobUrl; a.download = name; document.body.appendChild(a); a.click()
    document.body.removeChild(a); URL.revokeObjectURL(blobUrl)
  } catch { window.open(finalUrl, '_blank') }
}

function batchDownload() {
  if (!shareData.value?.share?.allow_download) { ElMessage.warning('此分享不允许下载'); return }
  const files = selectedFiles.value.filter(f => !f.is_dir && f.url)
  if (!files.length) { ElMessage.warning('没有可下载的文件'); return }
  files.forEach((f, i) => { setTimeout(() => downloadFile(f.url, f.name), i * 200) })
  ElMessage.success(`开始下载 ${files.length} 个文件`)
}

onMounted(() => {
  const code = route.params.code as string
  const savedPwd = localStorage.getItem(`share_pwd_${code}`)
  loadShare(savedPwd || undefined)
})
</script>

<style scoped>
.share-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

/* 密码卡片 */
.share-card {
  width: 100%;
  max-width: 700px;
  background: #fff;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}
.password-card { max-width: 400px; text-align: center; }
.lock-icon-wrap { display: flex; justify-content: center; margin-bottom: 8px; }
.lock-icon-bg {
  width: 80px; height: 80px; border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
}
.password-input :deep(.el-input__wrapper) { border-radius: 8px; box-shadow: 0 0 0 1px #dcdfe6 inset; padding: 4px 12px; }
.password-input :deep(.el-input__wrapper:focus-within) { box-shadow: 0 0 0 1px #667eea inset; }

/* 文件列表主区域 */
.share-main {
  width: 100%;
  max-width: 860px;
}

/* 顶部卡片 */
.share-header-card {
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(10px);
  border-radius: 16px 16px 0 0;
  padding: 24px 28px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
.share-header { display: flex; align-items: center; gap: 16px; }
.share-header-icon {
  width: 52px; height: 52px; border-radius: 14px;
  background: rgba(255,255,255,0.2);
  display: flex; align-items: center; justify-content: center;
}
.share-header-info h2 { margin: 0; font-size: 20px; color: #fff; font-weight: 700; }
.share-header-info p { margin: 4px 0 0; font-size: 13px; color: rgba(255,255,255,0.7); }

/* 有效期标识 */
.expire-badge {
  margin-left: auto;
  display: flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: 20px;
  font-size: 13px; font-weight: 600;
  flex-shrink: 0;
}
.expire-normal { background: rgba(255,255,255,0.2); color: #fff; }
.expire-urgent { background: #ff9500; color: #fff; }
.expire-expired { background: #f56c6c; color: #fff; }

/* 过期警告条 */
.expire-banner {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 20px;
  font-size: 13px; font-weight: 600;
}
.expire-banner-expired { background: #fef0f0; color: #f56c6c; }
.expire-banner-urgent { background: #fdf6ec; color: #e6a23c; }

/* 过期阻断 */
.expire-block {
  text-align: center; padding: 60px 20px;
  background: #fff;
  border-radius: 0 0 16px 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}
.expire-block-icon { margin-bottom: 8px; }

/* 工具栏 */
.share-toolbar {
  background: #fff;
  padding: 12px 24px;
  display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;
  border-bottom: 1px solid #f0f0f0;
}
.breadcrumb-bar { flex: 1; }
.breadcrumb-current { color: #303133; font-weight: 600; }
.batch-bar {
  display: flex; align-items: center; gap: 10px;
  font-size: 13px; color: #606266;
  background: #ecf5ff; padding: 4px 12px; border-radius: 6px;
}

/* 文件表格 */
.share-table-wrap {
  background: #fff;
  border-radius: 0 0 16px 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}
.file-table {
  width: 100%; border-collapse: collapse; font-size: 13px;
}
.file-table thead th {
  padding: 12px 16px; text-align: left;
  font-weight: 600; font-size: 12px; color: #909399;
  background: #fafafa; border-bottom: 1px solid #f0f0f0;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.file-table tbody tr { transition: background 0.15s; }
.file-table tbody tr:hover { background: #f5f7fa; }
.file-table tbody td {
  padding: 10px 16px; border-bottom: 1px solid #f5f5f5; color: #303133;
}
.file-table tbody tr:last-child td { border-bottom: none; }
.file-name-cell { display: flex; align-items: center; gap: 8px; }
.file-name-cell.clickable { cursor: pointer; }
.file-name-cell.clickable span { color: #409EFF; }
.cell-muted { color: #909399; font-size: 12px; }
.action-cell { display: flex; align-items: center; gap: 4px; }
.open-link { color: #409EFF; font-size: 12px; cursor: pointer; }
.open-link:hover { text-decoration: underline; }
.empty-cell { text-align: center; color: #c0c4cc; padding: 40px 0 !important; }
.row-dir td:first-child { /* directory row subtle highlight */ }

/* 底部 */
.share-footer {
  text-align: center; padding: 16px 0 0;
  font-size: 12px; color: rgba(255,255,255,0.5);
}
</style>

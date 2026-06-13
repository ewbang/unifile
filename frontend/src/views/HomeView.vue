<template>
  <div class="home-view">
    <!-- Top Header -->
    <div class="home-header">
      <div class="header-content">
        <div class="header-left">
          <div class="breadcrumb-area">
            <span class="storage-name" v-if="currentStorage">{{ currentStorage.name }}</span>
            <template v-if="currentStorage">
              <span class="breadcrumb-sep">></span>
              <template v-for="(crumb, idx) in breadcrumbs" :key="idx">
                <span class="crumb-item" :class="{ active: idx === breadcrumbs.length - 1 }">
                  <a v-if="idx < breadcrumbs.length - 1" @click.prevent="navigateTo(crumb.path)">{{ crumb.name }}</a>
                  <span v-else>{{ crumb.name }}</span>
                </span>
                <span v-if="idx < breadcrumbs.length - 1" class="breadcrumb-sep">></span>
              </template>
            </template>
            <span v-else class="site-title">{{ siteName }}</span>
          </div>
        </div>
        <div class="header-right">
          <!-- Storage Selector -->
          <el-select
            v-if="storages.length > 0"
            v-model="selectedStorageId"
            placeholder="选择存储源"
            class="storage-select"
            @change="onStorageChange"
            size="default"
          >
            <el-option
              v-for="s in storages"
              :key="s.id"
              :label="s.name"
              :value="s.id"
            >
              <div class="storage-option">
                <div class="storage-dot" :style="{ background: s.color || '#409EFF' }"></div>
                <span>{{ s.name }}</span>
              </div>
            </el-option>
          </el-select>
          
          <el-button class="login-btn" @click="$router.push('/login')">
            <el-icon style="margin-right: 4px"><User /></el-icon>
            登录
          </el-button>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="home-content">
      <!-- No Storage Selected -->
      <div v-if="!currentStorage" class="empty-state">
        <div class="empty-icon">
          <el-icon :size="64" color="#c0c4cc"><Folder /></el-icon>
        </div>
        <h3>欢迎访问 {{ siteName }}</h3>
        <p>请从右上角选择一个存储源开始浏览</p>
      </div>

      <!-- File Browser -->
      <div v-else class="file-browser">
        <div class="file-table-wrapper">
          <!-- Table Header -->
          <div class="file-table-header">
            <div class="col-checkbox">
              <el-checkbox v-model="allChecked" @change="onSelectAll" />
            </div>
            <div class="col-name">
              <span>文件名</span>
              <el-icon class="sort-icon"><Sort /></el-icon>
            </div>
            <div class="col-time">
              <span>修改时间</span>
              <el-icon class="sort-icon"><Sort /></el-icon>
            </div>
            <div class="col-size">
              <span>大小</span>
              <el-icon class="sort-icon"><Sort /></el-icon>
            </div>
            <div class="col-action">操作</div>
          </div>

          <!-- Table Body -->
          <div class="file-table-body" v-loading="loading">
            <!-- Back Row -->
            <div v-if="currentPath !== '/'" class="file-row" @click="goBack">
              <div class="col-checkbox"></div>
              <div class="col-name">
                <el-icon class="file-icon back-icon"><Back /></el-icon>
                <span class="file-name">..</span>
              </div>
              <div class="col-time">-</div>
              <div class="col-size">-</div>
              <div class="col-action"></div>
            </div>

            <!-- File Rows -->
            <div
              v-for="row in files"
              :key="row.path"
              class="file-row"
              :class="{ 'is-dir': row.is_dir, 'need-password': row.need_password }"
              @click="handleClick(row)"
              @dblclick="handleDblClick(row)"
              @contextmenu.prevent="onContextMenu($event, row)"
            >
              <div class="col-checkbox" @click.stop>
                <el-checkbox v-model="row._checked" :disabled="row.is_dir" @change="onRowCheck(row)" />
              </div>
              <div class="col-name">
                <FileIcon :name="row.name" :is-dir="row.is_dir" :size="20" />
                <span class="file-name">{{ row.name }}</span>
                <el-icon v-if="row.need_password" class="lock-icon" :size="14">
                  <Lock />
                </el-icon>
              </div>
              <div class="col-time">{{ row.last_modified || '-' }}</div>
              <div class="col-size">{{ row.is_dir ? '-' : formatSize(row.size) }}</div>
              <div class="col-action" @click.stop>
                <el-button
                  v-if="!row.is_dir"
                  type="primary"
                  link
                  size="small"
                  @click="downloadFile(row)"
                >
                  下载
                </el-button>
              </div>
            </div>

            <!-- Empty State -->
            <div v-if="!loading && files.length === 0" class="empty-row">
              <el-icon :size="48" color="#c0c4cc"><Folder /></el-icon>
              <p>此目录为空</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="home-footer">
      <p>Powered by {{ siteName }}</p>
    </div>

    <!-- Context Menu -->
    <div
      v-if="contextMenu.visible"
      class="context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
    >
      <div v-if="contextMenu.target?.is_dir" class="ctx-item" @click="handleCtxOpen">
        <el-icon><FolderOpened /></el-icon>
        <span>打开</span>
      </div>
      <template v-else>
        <div class="ctx-item" @click="handleCtxPreview">
          <el-icon><View /></el-icon>
          <span>预览</span>
        </div>
        <div class="ctx-item" @click="handleCtxDownload">
          <el-icon><Download /></el-icon>
          <span>下载</span>
        </div>
        <div class="ctx-item" @click="handleCtxCopyLink">
          <el-icon><Link /></el-icon>
          <span>复制直链</span>
        </div>
      </template>
      <div class="ctx-divider"></div>
      <div class="ctx-item" @click="handleCtxRefresh">
        <el-icon><Refresh /></el-icon>
        <span>刷新</span>
      </div>
    </div>

    <!-- Preview Dialog -->
    <el-dialog
      v-model="previewVisible"
      :title="previewFile?.name || '预览'"
      width="80%"
      destroy-on-close
      top="5vh"
    >
      <div class="preview-container">
        <img v-if="previewType === 'image'" :src="previewUrl" class="preview-image" />
        <video v-else-if="previewType === 'video'" :src="previewUrl" controls autoplay class="preview-video" />
        <iframe v-else-if="previewType === 'pdf'" :src="previewUrl" class="preview-pdf" />
        <div v-else class="preview-unsupported">
          <el-icon :size="48" color="#909399"><Document /></el-icon>
          <p>此文件类型不支持预览</p>
        </div>
      </div>
    </el-dialog>

    <!-- Password Dialog -->
    <el-dialog
      v-model="needPassword"
      width="420px"
      class="password-dialog"
      destroy-on-close
    >
      <div class="password-card">
        <div class="password-header">
          <div class="lock-circle">
            <el-icon :size="32" color="#fff"><Lock /></el-icon>
          </div>
          <h3>加密目录</h3>
          <p>请输入访问密码以继续</p>
        </div>
        
        <div class="password-body">
          <div class="path-display">
            <el-icon><Folder /></el-icon>
            <span>{{ passwordPath }}</span>
          </div>
          
          <el-input
            v-model="inputPassword"
            :type="showPassword ? 'text' : 'password'"
            placeholder="输入密码..."
            size="large"
            @keyup.enter="verifyAndLoad"
            class="pwd-input"
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
            <template #suffix>
              <el-icon 
                class="eye-toggle"
                @click="showPassword = !showPassword"
              >
                <View v-if="showPassword" />
                <Hide v-else />
              </el-icon>
            </template>
          </el-input>
          
          <el-button
            type="primary"
            size="large"
            class="verify-btn"
            :loading="verifying"
            @click="verifyAndLoad"
          >
            验证并访问
          </el-button>
          
          <p class="hint-text">
            <el-icon><InfoFilled /></el-icon>
            联系管理员获取访问密码
          </p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { homeApi, settingsApi } from '@/api'
import { ElMessage } from 'element-plus'
import FileIcon from '@/components/FileIcon.vue'

const route = useRoute()
const router = useRouter()

const siteName = ref('UniFile')
const storages = ref<any[]>([])
const selectedStorageId = ref<number | null>(null)
const currentStorage = ref<any>(null)
const files = ref<any[]>([])
const currentPath = ref('/')
const loading = ref(false)
const allChecked = ref(false)

// Password related
const needPassword = ref(false)
const inputPassword = ref('')
const showPassword = ref(false)
const verifying = ref(false)
const passwordPath = ref('')
const pathPasswords = ref<Record<string, string>>({})

// Context menu
const contextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  target: null as any,
})

// Preview
const previewVisible = ref(false)
const previewFile = ref<any>(null)
const previewUrl = ref('')
const previewType = ref('')

const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'bmp', 'ico', 'avif']
const videoExts = ['mp4', 'webm', 'ogg', 'mov', 'mkv', 'avi']
const pdfExts = ['pdf']

const breadcrumbs = computed(() => {
  if (!currentPath.value || currentPath.value === '/') return []
  const parts = currentPath.value.split('/').filter(Boolean)
  return parts.map((name, idx) => ({
    name,
    path: '/' + parts.slice(0, idx + 1).join('/'),
  }))
})

async function loadSiteSettings() {
  try {
    const res: any = await settingsApi.getPublic()
    if (res.site_name) siteName.value = res.site_name
  } catch {}
}

async function loadStorages() {
  try {
    storages.value = await homeApi.getPublicStorages() as any
    if (storages.value.length > 0) {
      selectedStorageId.value = storages.value[0].id
      onStorageChange(storages.value[0].id)
    }
  } catch {}
}

function onStorageChange(id: number) {
  const storage = storages.value.find(s => s.id === id)
  if (storage) {
    currentStorage.value = storage
    // 使用挂载路径作为起始路径，如果没有则从根目录开始
    const startPath = storage.mount_path || '/'
    currentPath.value = startPath
    pathPasswords.value = {}
    loadFiles(startPath)
  }
}

function findPasswordForPath(path: string): string | undefined {
  if (pathPasswords.value[path]) return pathPasswords.value[path]
  const parts = path.split('/')
  for (let i = parts.length - 1; i > 0; i--) {
    const parentPath = parts.slice(0, i).join('/') || '/'
    if (pathPasswords.value[parentPath]) return pathPasswords.value[parentPath]
  }
  return undefined
}

async function loadFiles(path: string, password?: string) {
  if (!currentStorage.value) return
  loading.value = true
  
  try {
    const res: any = await homeApi.listFiles(currentStorage.value.id, path, password)
    files.value = (res.files || []).map((f: any) => ({
      ...f,
      _checked: false,
      _password: password,
    }))
    currentPath.value = path
    if (password) {
      pathPasswords.value[path] = password
    }
  } catch (e: any) {
    const detail = e?.response?.data?.detail
    if (e?.response?.status === 401 && typeof detail === 'object' && detail?.need_password) {
      needPassword.value = true
      passwordPath.value = path
      inputPassword.value = pathPasswords.value[path] || ''
    } else {
      ElMessage.error(typeof detail === 'string' ? detail : '加载失败')
    }
  } finally {
    loading.value = false
  }
}

function handleClick(row: any) {
  if (row.is_dir) {
    const password = findPasswordForPath(row.path)
    loadFiles(row.path, password)
  }
}

function handleDblClick(row: any) {
  if (!row.is_dir && row.url) {
    window.open(row.url, '_blank')
  }
}

function navigateTo(path: string) {
  const password = findPasswordForPath(path)
  loadFiles(path, password)
}

function goBack() {
  const parts = currentPath.value.split('/').filter(Boolean)
  parts.pop()
  const parentPath = parts.length ? '/' + parts.join('/') : '/'
  const password = findPasswordForPath(parentPath)
  loadFiles(parentPath, password)
}

async function verifyAndLoad() {
  if (!inputPassword.value) {
    ElMessage.warning('请输入密码')
    return
  }
  verifying.value = true
  try {
    await homeApi.verifyPassword(currentStorage.value.id, passwordPath.value, inputPassword.value)
    needPassword.value = false
    loadFiles(passwordPath.value, inputPassword.value)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '密码错误')
  } finally {
    verifying.value = false
  }
}

function onSelectAll(val: boolean) {
  files.value.forEach((f: any) => {
    if (!f.is_dir) f._checked = val
  })
}

function onRowCheck(row: any) {
  const checkedFiles = files.value.filter((f: any) => !f.is_dir && f._checked)
  allChecked.value = checkedFiles.length === files.value.filter((f: any) => !f.is_dir).length && checkedFiles.length > 0
}

async function downloadFile(row: any) {
  if (!currentStorage.value) return
  try {
    const password = findPasswordForPath(currentPath.value)
    const downloadUrl = `/api/home/${currentStorage.value.id}/download?path=${encodeURIComponent(row.path)}${password ? `&password=${encodeURIComponent(password)}` : ''}`
    
    // 先请求后端，判断返回类型
    const resp = await fetch(downloadUrl)
    if (!resp.ok) {
      throw new Error('下载失败')
    }
    
    const contentType = resp.headers.get('content-type') || ''
    let fileUrl = downloadUrl
    
    if (contentType.includes('application/json')) {
      // 云存储返回的是JSON（含签名URL），提取真实URL
      const data = await resp.json()
      if (data.url) {
        fileUrl = data.url
      } else {
        throw new Error('获取下载链接失败')
      }
    }
    
    // 用 fetch + blob 强制下载，避免浏览器预览
    try {
      const fileResp = await fetch(fileUrl)
      if (!fileResp.ok) throw new Error('下载失败')
      const blob = await fileResp.blob()
      const blobUrl = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = row.name
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(blobUrl)
    } catch {
      // 跨域失败时降级为直接打开
      window.open(fileUrl, '_blank')
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '下载失败')
  }
}

function formatSize(size: number | null): string {
  if (!size) return '-'
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  if (size < 1024 * 1024 * 1024) return (size / (1024 * 1024)).toFixed(1) + ' MB'
  return (size / (1024 * 1024 * 1024)).toFixed(1) + ' GB'
}

// Context menu
function onContextMenu(e: MouseEvent, row: any) {
  contextMenu.visible = true
  contextMenu.x = e.clientX
  contextMenu.y = e.clientY
  contextMenu.target = row
}

function closeContextMenu() {
  contextMenu.visible = false
}

function handleCtxOpen() {
  if (contextMenu.target) {
    handleClick(contextMenu.target)
  }
  closeContextMenu()
}

function handleCtxDownload() {
  if (contextMenu.target) {
    downloadFile(contextMenu.target)
  }
  closeContextMenu()
}

function handleCtxPreview() {
  const row = contextMenu.target
  if (!row) return
  
  const ext = row.name.includes('.') ? row.name.split('.').pop()?.toLowerCase() : ''
  
  if (imageExts.includes(ext)) {
    previewType.value = 'image'
  } else if (videoExts.includes(ext)) {
    previewType.value = 'video'
  } else if (pdfExts.includes(ext)) {
    previewType.value = 'pdf'
  } else {
    previewType.value = ''
  }
  
  previewFile.value = row
  const password = findPasswordForPath(currentPath.value)
  const serveUrl = `/api/home/${currentStorage.value.id}/download?path=${encodeURIComponent(row.path)}${password ? `&password=${encodeURIComponent(password)}` : ''}`
  previewUrl.value = serveUrl
  previewVisible.value = true
  closeContextMenu()
}

async function handleCtxCopyLink() {
  const row = contextMenu.target
  if (!row) return
  
  try {
    const password = findPasswordForPath(currentPath.value)
    const downloadUrl = `/api/home/${currentStorage.value.id}/download?path=${encodeURIComponent(row.path)}${password ? `&password=${encodeURIComponent(password)}` : ''}`
    
    // 请求后端获取直链
    const resp = await fetch(downloadUrl)
    if (!resp.ok) throw new Error('获取链接失败')
    
    const contentType = resp.headers.get('content-type') || ''
    let directUrl = downloadUrl
    
    if (contentType.includes('application/json')) {
      const data = await resp.json()
      if (data.url) {
        directUrl = data.url
      }
    } else {
      // 本地存储，拼接完整URL
      directUrl = `${window.location.origin}${downloadUrl}`
    }
    
    await navigator.clipboard.writeText(directUrl)
    ElMessage.success('直链已复制')
  } catch {
    ElMessage.error('复制失败')
  }
  closeContextMenu()
}

function handleCtxRefresh() {
  loadFiles(currentPath.value)
  closeContextMenu()
}

onMounted(() => {
  loadSiteSettings()
  loadStorages()
  // Close context menu on click elsewhere
  document.addEventListener('click', closeContextMenu)
})
</script>

<style scoped>
.home-view {
  min-height: 100vh;
  background: #f0f2f5;
  display: flex;
  flex-direction: column;
}

/* Header */
.home-header {
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.breadcrumb-area {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.site-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.storage-name {
  font-weight: 600;
  color: #303133;
}

.breadcrumb-sep {
  color: #c0c4cc;
  margin: 0 4px;
}

.crumb-item {
  color: #606266;
}

.crumb-item.active {
  color: #303133;
  font-weight: 500;
}

.crumb-item a {
  color: #409eff;
  text-decoration: none;
  cursor: pointer;
}

.crumb-item a:hover {
  color: #66b1ff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.storage-select {
  width: 200px;
}

.storage-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.storage-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.login-btn {
  border-radius: 6px;
}

/* Main Content */
.home-content {
  flex: 1;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  padding: 24px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 120px 20px;
  text-align: center;
}

.empty-icon {
  margin-bottom: 24px;
  opacity: 0.5;
}

.empty-state h3 {
  font-size: 20px;
  color: #303133;
  margin: 0 0 8px;
}

.empty-state p {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

/* File Table */
.file-table-wrapper {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.file-table-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #ebeef5;
  font-size: 13px;
  font-weight: 600;
  color: #606266;
}

.sort-icon {
  font-size: 12px;
  color: #c0c4cc;
  cursor: pointer;
}

.sort-icon:hover {
  color: #409eff;
}

.col-checkbox {
  width: 40px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.col-name {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  padding-right: 16px;
}

.col-name .file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.col-time {
  width: 180px;
  flex-shrink: 0;
  font-size: 13px;
  color: #909399;
  text-align: center;
}

.col-size {
  width: 100px;
  flex-shrink: 0;
  text-align: center;
  font-size: 13px;
  color: #909399;
}

.col-action {
  width: 80px;
  flex-shrink: 0;
  text-align: center;
}

.file-table-body {
  min-height: 200px;
}

.file-row {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background 0.15s ease;
}

.file-row:last-child {
  border-bottom: none;
}

.file-row:hover {
  background: #f5f7fa;
}

.file-row.is-dir:hover {
  background: #ecf5ff;
}

.file-row.need-password {
  opacity: 0.7;
}

.file-icon {
  color: #409eff;
  font-size: 18px;
}

.back-icon {
  color: #909399;
}

.file-name {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.lock-icon {
  color: #e6a23c;
  margin-left: 4px;
}

.empty-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-row p {
  margin: 12px 0 0;
  font-size: 14px;
}

/* Footer */
.home-footer {
  text-align: center;
  padding: 20px;
  color: #909399;
  font-size: 13px;
}

/* Password Dialog */
.password-dialog :deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
  padding: 0;
}

.password-dialog :deep(.el-dialog__header) {
  display: none;
}

.password-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.password-card {
  background: #fff;
}

.password-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 32px 24px 24px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.password-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='40' height='40' viewBox='0 0 40 40' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M20 20h20v20H20z'/%3E%3C/g%3E%3C/svg%3E");
}

.lock-circle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
  backdrop-filter: blur(10px);
}

.password-header h3 {
  font-size: 20px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 8px;
}

.password-header p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
}

.password-body {
  padding: 24px;
}

.path-display {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #606266;
}

.path-display .el-icon {
  color: #409eff;
}

.pwd-input {
  margin-bottom: 16px;
}

.pwd-input :deep(.el-input__wrapper) {
  border-radius: 8px;
}

.eye-toggle {
  cursor: pointer;
  color: #c0c4cc;
  transition: color 0.2s;
}

.eye-toggle:hover {
  color: #606266;
}

.verify-btn {
  width: 100%;
  height: 44px;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 500;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  margin-bottom: 16px;
}

.verify-btn:hover {
  opacity: 0.9;
}

.hint-text {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
  margin: 0;
}

/* Context Menu */
.context-menu {
  position: fixed;
  z-index: 2000;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  padding: 6px 0;
  min-width: 160px;
}

.ctx-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  font-size: 14px;
  color: #303133;
  cursor: pointer;
  transition: background 0.15s;
}

.ctx-item:hover {
  background: #f5f7fa;
  color: #409eff;
}

.ctx-item .el-icon {
  font-size: 16px;
  color: #909399;
}

.ctx-item:hover .el-icon {
  color: #409eff;
}

.ctx-divider {
  height: 1px;
  background: #ebeef5;
  margin: 4px 0;
}

/* Preview Dialog */
.preview-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.preview-image {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
}

.preview-video {
  max-width: 100%;
  max-height: 80vh;
}

.preview-pdf {
  width: 100%;
  height: 80vh;
  border: none;
}

.preview-unsupported {
  text-align: center;
  color: #909399;
  padding: 40px;
}

.preview-unsupported p {
  margin: 12px 0 0;
  font-size: 14px;
}
</style>
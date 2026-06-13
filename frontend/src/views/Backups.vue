<template>
  <div class="backups-page">
    <!-- 数据库信息卡片 -->
    <el-card class="db-info-card" shadow="never">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span style="font-weight: 600">数据库信息</span>
          <el-button size="small" @click="loadDbInfo"><el-icon style="margin-right: 4px"><Refresh /></el-icon>刷新</el-button>
        </div>
      </template>
      <div v-if="dbInfo.exists" class="db-info-grid">
        <div class="info-item">
          <span class="info-label">数据库路径</span>
          <span class="info-value" style="font-family: monospace; font-size: 12px">{{ dbInfo.path }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">文件大小</span>
          <span class="info-value">{{ dbInfo.size_text }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">最后修改</span>
          <span class="info-value">{{ dbInfo.modified_at?.replace('T', ' ').slice(0, 19) }}</span>
        </div>
      </div>
      <div v-if="dbInfo.tables?.length > 0" style="margin-top: 16px">
        <div style="font-size: 13px; color: #606266; margin-bottom: 8px">数据表统计</div>
        <div class="table-stats">
          <el-tag v-for="table in dbInfo.tables" :key="table" size="small" style="margin: 0 8px 8px 0">
            {{ table }}: {{ dbInfo.table_counts?.[table] ?? '-' }} 条
          </el-tag>
        </div>
      </div>
    </el-card>

    <!-- 操作栏 -->
    <div class="action-bar">
      <el-button type="primary" @click="createBackup" :loading="creating">
        <el-icon style="margin-right: 4px"><FolderAdd /></el-icon>
        创建备份
      </el-button>
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :show-file-list="false"
        accept=".db"
        :on-change="handleUploadChange"
      >
        <el-button>
          <el-icon style="margin-right: 4px"><Upload /></el-icon>
          上传备份
        </el-button>
      </el-upload>
      <div style="flex: 1"></div>
      <span style="font-size: 13px; color: #909399">共 {{ backups.length }} 个备份</span>
    </div>

    <!-- 备份列表 -->
    <el-card shadow="never" v-loading="loading">
      <el-empty v-if="!loading && backups.length === 0" description="暂无备份" />
      <div v-else class="backup-list">
        <div v-for="backup in backups" :key="backup.filename" class="backup-item">
          <div class="backup-icon">
            <el-icon :size="24" color="#409EFF"><Coin /></el-icon>
          </div>
          <div class="backup-info">
            <div class="backup-name">{{ backup.filename }}</div>
            <div class="backup-meta">
              <span>{{ backup.size_text }}</span>
              <span class="meta-divider">|</span>
              <span>{{ backup.created_at?.replace('T', ' ').slice(0, 19) }}</span>
            </div>
          </div>
          <div class="backup-actions">
            <el-button size="small" type="primary" link @click="downloadBackup(backup)">
              <el-icon style="margin-right: 4px"><Download /></el-icon>
              下载
            </el-button>
            <el-button size="small" type="warning" link @click="confirmRestore(backup)">
              <el-icon style="margin-right: 4px"><RefreshRight /></el-icon>
              还原
            </el-button>
            <el-popconfirm title="确定删除此备份?" @confirm="deleteBackup(backup.filename)">
              <template #reference>
                <el-button size="small" type="danger" link>
                  <el-icon style="margin-right: 4px"><Delete /></el-icon>
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>
      </div>
      <!-- 分页 -->
      <div v-if="pagination.total > 0" style="margin-top: 16px; display: flex; justify-content: flex-end">
        <el-pagination
          v-model:current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="loadBackups"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const api = axios.create({ baseURL: '/api' })
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

const loading = ref(false)
const creating = ref(false)
const backups = ref<any[]>([])
const uploadRef = ref()
const pagination = reactive({ page: 1, pageSize: 4, total: 0 })

const dbInfo = reactive({
  exists: false,
  path: '',
  size: 0,
  size_text: '',
  modified_at: '',
  tables: [] as string[],
  table_counts: {} as Record<string, number>,
})

async function loadDbInfo() {
  try {
    const res: any = await api.get('/backups/db-info')
    Object.assign(dbInfo, res)
  } catch {}
}

async function loadBackups() {
  loading.value = true
  try {
    const res: any = await api.get('/backups/', { params: { page: pagination.page, page_size: pagination.pageSize } })
    backups.value = res.backups || []
    pagination.total = res.total || 0
  } catch {} finally {
    loading.value = false
  }
}

async function createBackup() {
  creating.value = true
  try {
    const res: any = await api.post('/backups/create')
    ElMessage.success(res.message || '备份创建成功')
    await loadBackups()
    await loadDbInfo()
  } catch {} finally {
    creating.value = false
  }
}

async function downloadBackup(backup: any) {
  try {
    const token = localStorage.getItem('token')
    const response = await fetch(`/api/backups/download/${backup.filename}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (!response.ok) throw new Error('下载失败')
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = backup.filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('下载成功')
  } catch (e: any) {
    ElMessage.error(e.message || '下载失败')
  }
}

async function confirmRestore(backup: any) {
  try {
    await ElMessageBox.confirm(
      `确定要从备份 "${backup.filename}" 还原数据库吗？\n\n还原前会自动备份当前数据库。`,
      '确认还原',
      { type: 'warning', confirmButtonText: '确定还原', cancelButtonText: '取消' }
    )
    await restoreBackup(backup.filename)
  } catch {}
}

async function restoreBackup(filename: string) {
  try {
    const res: any = await api.post(`/backups/restore/${filename}`)
    ElMessage.success(res.message || '还原成功')
    await loadBackups()
    await loadDbInfo()
  } catch {}
}

async function deleteBackup(filename: string) {
  try {
    await api.delete(`/backups/${filename}`)
    ElMessage.success('备份已删除')
    await loadBackups()
  } catch {}
}

async function handleUploadChange(file: any) {
  if (!file) return
  const formData = new FormData()
  formData.append('file', file.raw)
  try {
    const token = localStorage.getItem('token')
    const response = await fetch('/api/backups/upload', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    })
    const res = await response.json()
    if (response.ok) {
      ElMessage.success(res.message || '上传成功')
      await loadBackups()
    } else {
      ElMessage.error(res.detail || '上传失败')
    }
  } catch (e: any) {
    ElMessage.error(e.message || '上传失败')
  }
}

onMounted(() => {
  loadDbInfo()
  loadBackups()
})
</script>

<style scoped>
.backups-page {
  max-width: 1000px;
  margin: 0 auto;
}

.db-info-card {
  margin-bottom: 16px;
}

.db-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: #909399;
}

.info-value {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.table-stats {
  display: flex;
  flex-wrap: wrap;
}

.action-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.backup-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.backup-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: background 0.2s;
}

.backup-item:hover {
  background: #ecf5ff;
}

.backup-icon {
  width: 48px;
  height: 48px;
  background: #ecf5ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.backup-info {
  flex: 1;
  min-width: 0;
}

.backup-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  font-family: monospace;
}

.backup-meta {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.meta-divider {
  margin: 0 8px;
}

.backup-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}
</style>
<template>
  <div class="logs-page">
    <!-- 统计 -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-num">{{ stats.total }}</span>
        <span class="stat-label">总操作</span>
      </div>
      <div class="stat-item">
        <span class="stat-num" style="color:#409EFF">{{ stats.downloads }}</span>
        <span class="stat-label">下载</span>
      </div>
      <div class="stat-item">
        <span class="stat-num" style="color:#67c23a">{{ stats.uploads }}</span>
        <span class="stat-label">上传</span>
      </div>
      <div class="stat-item">
        <span class="stat-num" style="color:#f56c6c">{{ stats.deletes }}</span>
        <span class="stat-label">删除</span>
      </div>
    </div>

    <!-- 筛选 -->
    <el-card style="margin-bottom:12px">
      <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap">
        <el-select v-model="filters.operation" placeholder="操作类型" clearable size="small" style="width:120px" @change="loadLogs">
          <el-option label="全部" value="" />
          <el-option label="下载" value="download" />
          <el-option label="上传" value="upload" />
          <el-option label="删除" value="delete" />
          <el-option label="移动" value="move" />
          <el-option label="复制" value="copy" />
          <el-option label="分享" value="share" />
        </el-select>
        <el-input v-model="filters.keyword" placeholder="搜索文件名" clearable size="small" style="width:200px" @keyup.enter="loadLogs" @clear="loadLogs" />
        <el-button size="small" @click="loadLogs"><el-icon style="margin-right:4px"><Refresh /></el-icon>刷新</el-button>
        <el-popconfirm title="确定清空所有操作日志?此操作不可恢复!" @confirm="clearLogs" v-if="perm('logs')">
          <template #reference>
            <el-button size="small" type="danger"><el-icon style="margin-right:4px"><Delete /></el-icon>清空日志</el-button>
          </template>
        </el-popconfirm>
      </div>
    </el-card>

    <!-- 表格 -->
    <el-card v-loading="loading">
      <el-table :data="logs" stripe style="width:100%" empty-text="暂无日志">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户" width="100" />
        <el-table-column prop="storage_name" label="存储源" width="100" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-tag :type="opType(row.operation)" size="small">{{ opLabel(row.operation) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="file_name" label="文件" min-width="200" show-overflow-tooltip />
        <el-table-column label="大小" width="90">
          <template #default="{ row }">{{ row.file_size ? formatSize(row.file_size) : '-' }}</template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP" width="130" />
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{ row }">{{ row.created_at?.replace('T', ' ').slice(0, 19) }}</template>
        </el-table-column>
      </el-table>
      <div style="margin-top:16px; display:flex; justify-content:flex-end">
        <el-pagination
          v-model:current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          layout="total, prev, pager, next"
          @current-change="loadLogs"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { logsApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const perm = (code: string) => userStore.hasPermission(code)

const logs = ref<any[]>([])
const loading = ref(false)
const stats = reactive({ total: 0, downloads: 0, uploads: 0, deletes: 0 })
const filters = reactive({ operation: '', keyword: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

function formatSize(bytes: number): string {
  if (!bytes) return '0 B'
  const u = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + u[i]
}

const opMap: Record<string, { label: string; type: string }> = {
  download: { label: '下载', type: '' },
  upload: { label: '上传', type: 'success' },
  delete: { label: '删除', type: 'danger' },
  move: { label: '移动', type: 'warning' },
  copy: { label: '复制', type: 'info' },
  share: { label: '分享', type: 'success' },
  mkdir: { label: '新建', type: '' },
}
function opLabel(op: string) { return opMap[op]?.label || op }
function opType(op: string) { return opMap[op]?.type || '' }

async function loadLogs() {
  loading.value = true
  try {
    const res: any = await logsApi.list({
      page: pagination.page, page_size: pagination.pageSize,
      operation: filters.operation || undefined,
      keyword: filters.keyword || undefined,
    })
    logs.value = res.items; pagination.total = res.total
  } catch {} finally { loading.value = false }
}

async function loadStats() {
  try { const res: any = await logsApi.stats(); Object.assign(stats, res) } catch {}
}

onMounted(() => { loadLogs(); loadStats() })

async function clearLogs() {
  try {
    await logsApi.clear()
    ElMessage.success('日志已清空')
    await loadLogs()
    await loadStats()
  } catch {}
}
</script>

<style scoped>
.logs-page { max-width: 1200px; margin: 0 auto; }
.stats-bar { display: flex; gap: 12px; margin-bottom: 12px; }
.stat-item {
  flex: 1; background: #fff; border-radius: 10px; padding: 14px 16px;
  display: flex; flex-direction: column; align-items: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.stat-num { font-size: 22px; font-weight: 700; color: #303133; line-height: 1; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
</style>

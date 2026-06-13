<template>
  <div class="login-logs-page">
    <!-- 统计 -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-num">{{ stats.total }}</span>
        <span class="stat-label">总登录</span>
      </div>
      <div class="stat-item">
        <span class="stat-num" style="color:#67c23a">{{ stats.success }}</span>
        <span class="stat-label">成功</span>
      </div>
      <div class="stat-item">
        <span class="stat-num" style="color:#f56c6c">{{ stats.failed }}</span>
        <span class="stat-label">失败</span>
      </div>
    </div>

    <!-- 筛选 -->
    <el-card style="margin-bottom:12px">
      <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap">
        <el-input v-model="filters.username" placeholder="用户名" clearable size="small" style="width:150px" @keyup.enter="loadLogs" @clear="loadLogs" />
        <el-select v-model="filters.status" placeholder="状态" clearable size="small" style="width:100px" @change="loadLogs">
          <el-option label="全部" value="" />
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
        </el-select>
        <el-button size="small" @click="loadLogs"><el-icon style="margin-right:4px"><Refresh /></el-icon>刷新</el-button>
        <el-popconfirm title="确定清空所有登录日志?" @confirm="clearLogs" v-if="perm('logs')">
          <template #reference>
            <el-button size="small" type="danger"><el-icon style="margin-right:4px"><Delete /></el-icon>清空</el-button>
          </template>
        </el-popconfirm>
      </div>
    </el-card>

    <!-- 表格 -->
    <el-card v-loading="loading">
      <el-table :data="logs" stripe style="width:100%" empty-text="暂无登录日志">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'danger'" size="small">{{ row.status === 'success' ? '成功' : '失败' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="备注" width="150" />
        <el-table-column prop="ip_address" label="IP 地址" width="140" />
        <el-table-column label="浏览器" min-width="200">
          <template #default="{ row }">
            <BrowserIcon :user-agent="row.user_agent" :size="22" :show-name="true" />
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="登录时间" width="170">
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
import { loginLogsApi } from '@/api'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'
import BrowserIcon from '@/components/BrowserIcon.vue'

const userStore = useUserStore()
const perm = (code: string) => userStore.hasPermission(code)

const logs = ref<any[]>([])
const loading = ref(false)
const stats = reactive({ total: 0, success: 0, failed: 0 })
const filters = reactive({ username: '', status: '' })
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })

async function loadLogs() {
  loading.value = true
  try {
    const res: any = await loginLogsApi.list({
      page: pagination.page, page_size: pagination.pageSize,
      username: filters.username || undefined,
      status: filters.status || undefined,
    })
    logs.value = res.items; pagination.total = res.total
  } catch {} finally { loading.value = false }
}

async function loadStats() {
  try { const res: any = await loginLogsApi.stats(); Object.assign(stats, res) } catch {}
}

async function clearLogs() {
  try {
    await loginLogsApi.clear()
    ElMessage.success('登录日志已清空')
    await loadLogs()
    await loadStats()
  } catch {}
}

onMounted(() => { loadLogs(); loadStats() })
</script>

<style scoped>
.login-logs-page { max-width: 1200px; margin: 0 auto; }
.stats-bar { display: flex; gap: 12px; margin-bottom: 12px; }
.stat-item {
  flex: 1; background: #fff; border-radius: 10px; padding: 14px 16px;
  display: flex; flex-direction: column; align-items: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.stat-num { font-size: 22px; font-weight: 700; color: #303133; line-height: 1; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }
</style>

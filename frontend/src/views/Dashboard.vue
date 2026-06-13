<template>
  <div class="dashboard-page">
    <!-- Stats cards -->
    <div class="stats-bar">
      <div class="stat-card" v-for="card in statCards" :key="card.label" :style="{ cursor: card.action ? 'pointer' : 'default' }" @click="card.action?.()">
        <div class="stat-info">
          <div class="stat-label">{{ card.label }}</div>
          <div class="stat-num">{{ card.value }}</div>
        </div>
        <el-icon :size="36" :color="card.color"><component :is="card.icon" /></el-icon>
      </div>
    </div>

    <div style="display: flex; gap: 16px">
      <!-- 存储源 -->
      <el-card style="flex: 1">
        <template #header>
          <div style="display: flex; align-items: center; justify-content: space-between">
            <span style="font-weight: 600">存储源</span>
            <el-button type="primary" size="small" link @click="$router.push('/admin/storages')">管理 →</el-button>
          </div>
        </template>
        <div v-if="storages.length === 0" style="text-align: center; padding: 32px; color: #909399">
          还没有存储源
        </div>
        <div v-else class="storage-list">
          <div v-for="s in storages" :key="s.id" class="storage-item" @click="$router.push(`/admin/files/${s.id}`)">
            <div class="storage-dot" :style="{ background: s.color }" />
            <span class="storage-name">{{ s.name }}</span>
            <el-tag :type="s.enabled ? 'success' : 'info'" size="small">{{ typeNames[s.storage_type] || s.storage_type }}</el-tag>
          </div>
        </div>
      </el-card>

      <!-- 最近操作 -->
      <el-card style="flex: 1">
        <template #header>
          <div style="display: flex; align-items: center; justify-content: space-between">
            <span style="font-weight: 600">最近操作</span>
            <el-button type="primary" size="small" link @click="$router.push('/admin/logs')">查看全部 →</el-button>
          </div>
        </template>
        <div v-if="recentLogs.length === 0" style="text-align: center; padding: 32px; color: #909399">
          暂无操作记录
        </div>
        <div v-else class="log-list">
          <div v-for="log in recentLogs" :key="log.id" class="log-item">
            <el-tag :type="opType(log.operation)" size="small" style="width: 48px; text-align: center">{{ opLabel(log.operation) }}</el-tag>
            <span class="log-user">{{ log.username }}</span>
            <span class="log-file">{{ log.file_name }}</span>
            <span class="log-time">{{ log.created_at?.replace('T', ' ').slice(0, 19) }}</span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storageApi, dashboardApi } from '@/api'

const router = useRouter()
const storages = ref<any[]>([])
const dashStats = ref<any>({})
const recentLogs = ref<any[]>([])

const typeNames: Record<string, string> = {
  aliyun: '阿里云', huawei: '华为云', tencent: '腾讯云', baidu: '百度云',
  upyun: '又拍云', qiniu: '七牛云', volcengine: '火山引擎', local: '本地',
}

const opMap: Record<string, { label: string; type: string }> = {
  download: { label: '下载', type: '' }, upload: { label: '上传', type: 'success' },
  delete: { label: '删除', type: 'danger' }, move: { label: '移动', type: 'warning' },
  copy: { label: '复制', type: 'info' }, share: { label: '分享', type: 'success' },
  mkdir: { label: '新建', type: '' }, rename: { label: '重命名', type: 'warning' },
}
function opLabel(op: string) { return opMap[op]?.label || op }
function opType(op: string) { return opMap[op]?.type || '' }

const statCards = computed(() => [
  { label: '存储源', value: dashStats.value.storage_count ?? storages.value.length, icon: 'Box', color: '#409EFF', action: () => router.push('/admin/storages') },
  { label: '分享链接', value: dashStats.value.share_count ?? 0, icon: 'Share', color: '#67c23a', action: () => router.push('/admin/shares') },
  { label: '用户数', value: dashStats.value.user_count ?? 0, icon: 'User', color: '#e6a23c', action: () => router.push('/admin/users') },
  { label: '操作记录', value: dashStats.value.log_count ?? 0, icon: 'Document', color: '#909399', action: () => router.push('/admin/logs') },
])

onMounted(async () => {
  try { storages.value = await storageApi.list() as any } catch {}
  try {
    const res: any = await dashboardApi.stats()
    dashStats.value = res
    recentLogs.value = res.recent_logs || []
  } catch {}
})
</script>

<style scoped>
.dashboard-page { max-width: 1200px; margin: 0 auto; }
.stats-bar { display: flex; gap: 16px; margin-bottom: 16px; }
.stat-card {
  flex: 1; background: #fff; border-radius: 12px; padding: 20px;
  display: flex; align-items: center; justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  transition: box-shadow 0.2s;
}
.stat-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
.stat-label { font-size: 13px; color: #909399; }
.stat-num { font-size: 28px; font-weight: 700; color: #303133; margin-top: 4px; }

.storage-list { display: flex; flex-direction: column; gap: 8px; }
.storage-item {
  display: flex; align-items: center; gap: 10px; padding: 10px 12px;
  background: #fafafa; border-radius: 8px; cursor: pointer; transition: background 0.2s;
}
.storage-item:hover { background: #f0f9ff; }
.storage-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.storage-name { font-weight: 600; font-size: 13px; flex: 1; }

.log-list { display: flex; flex-direction: column; gap: 10px; }
.log-item { display: flex; align-items: center; gap: 10px; font-size: 13px; }
.log-user { color: #606266; width: 60px; flex-shrink: 0; }
.log-file { flex: 1; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.log-time { color: #c0c4cc; font-size: 12px; flex-shrink: 0; }
</style>

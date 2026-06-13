<template>
  <div class="shares-page">
    <!-- 顶部统计 -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-num">{{ shares.length }}</span>
        <span class="stat-label">总分享</span>
      </div>
      <div class="stat-item">
        <span class="stat-num" style="color:#67c23a">{{ shares.filter(s => s.enabled).length }}</span>
        <span class="stat-label">已启用</span>
      </div>
      <div class="stat-item">
        <span class="stat-num" style="color:#f56c6c">{{ shares.filter(s => !s.enabled).length }}</span>
        <span class="stat-label">已停用</span>
      </div>
      <div class="stat-item">
        <span class="stat-num" style="color:#e6a23c">{{ shares.filter(s => s.expire_at && new Date(s.expire_at).getTime() < Date.now()).length }}</span>
        <span class="stat-label">已过期</span>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="filter-group">
        <el-select
          v-model="filterStorageName"
          placeholder="所有存储源"
          clearable
          size="small"
          style="width: 150px"
          @change="onFilterChange"
        >
          <el-option
            v-for="name in storageNames"
            :key="name"
            :label="name"
            :value="name"
          />
        </el-select>
      </div>
      <transition name="el-fade-in">
        <div v-if="selected.length > 0" class="batch-info">
          <span>已选 <b>{{ selected.length }}</b> 项</span>
          <el-button text size="small" @click="clearSelection">取消</el-button>
          <el-button type="danger" size="small" @click="batchDelete">批量取消</el-button>
        </div>
      </transition>
      <el-button size="small" @click="loadShares"><el-icon style="margin-right:4px"><Refresh /></el-icon>刷新</el-button>
    </div>

    <!-- 表格 -->
    <div class="table-card" v-loading="loading">
      <table class="shares-table">
        <thead>
          <tr>
            <th style="width:36px">
              <el-checkbox v-model="allChecked" :indeterminate="isIndeterminate" @change="onSelectAll" />
            </th>
            <th style="width:36px"></th>
            <th style="width:20%">文件</th>
            <th style="width:70px">存储源</th>
            <th style="width:110px">链接</th>
            <th style="width:65px">状态</th>
            <th style="width:60px">访问</th>
            <th style="width:75px">有效期</th>
            <th style="width:70px">密码</th>
            <th style="width:140px">分享时间</th>
            <th style="width:130px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in shares" :key="row.id" :class="{ 'row-disabled': !row.enabled }">
            <td>
              <el-checkbox v-model="row._checked" @change="(val: boolean) => onRowCheck(row, val)" />
            </td>
            <td>
              <FileIcon :name="row.file_name" :is-dir="row.is_dir && !row.is_multi" :size="18" />
            </td>
            <td>
              <span class="file-name" :title="row.file_name">{{ row.file_name }}</span>
            </td>
            <td>
              <span class="cell-muted">{{ row.storage_name || '-' }}</span>
            </td>
            <td>
              <div class="link-cell">
                <el-button size="small" type="success" link @click="copyUrl(row)">复制</el-button>
                <el-button size="small" type="primary" link @click="openUrl(row)">打开</el-button>
              </div>
            </td>
            <td>
              <el-switch v-model="row.enabled" @change="toggleShare(row)" size="small" />
            </td>
            <td>
              <span class="cell-muted">{{ row.view_count }}{{ row.max_views ? '/' + row.max_views : '' }}</span>
            </td>
            <td>
              <span v-if="!row.expire_at" class="tag-permanent">永久</span>
              <span v-else-if="isExpired(row.expire_at)" class="tag-expired">过期</span>
              <span v-else class="tag-active">{{ formatExpire(row.expire_at) }}</span>
            </td>
            <td>
              <span v-if="row.password" class="pwd-text" :title="'点击复制: ' + row.password" @click="copyPwd(row.password)">{{ row.password }}</span>
              <span v-else class="cell-muted">-</span>
            </td>
            <td>
              <span class="cell-muted">{{ row.created_at?.replace('T', ' ').slice(0, 19) }}</span>
            </td>
            <td>
              <div class="action-cell">
                <el-button size="small" type="primary" link @click="openEdit(row)">编辑</el-button>
                <el-popconfirm title="确定取消此分享?" @confirm="deleteShare(row.id)">
                  <template #reference>
                    <el-button size="small" type="danger" link>删除</el-button>
                  </template>
                </el-popconfirm>
              </div>
            </td>
          </tr>
          <tr v-if="!loading && shares.length === 0">
            <td colspan="11" class="empty-cell">
              <el-icon :size="32" color="#c0c4cc"><Share /></el-icon>
              <p>暂无分享链接</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <div style="margin-top:12px; display:flex; justify-content:flex-end">
      <el-pagination
        v-model:current-page="pagination.page"
        :page-size="pagination.pageSize"
        :total="pagination.total"
        layout="total, prev, pager, next"
        @current-change="loadShares"
      />
    </div>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="editDialog.visible" title="编辑分享" width="480px" destroy-on-close>
      <el-form label-width="100px">
        <el-form-item label="文件"><span>{{ editDialog.file_name }}</span></el-form-item>
        <el-form-item label="访问密码">
          <div style="display:flex; align-items:center; gap:12px; width:100%">
            <el-switch v-model="editDialog.passwordEnabled" @change="(val: boolean) => { if (!val) editDialog.password = '' }" />
            <el-input v-if="editDialog.passwordEnabled" v-model="editDialog.password" placeholder="请输入密码" clearable style="flex:1">
              <template #append>
                <el-button @click="editDialog.password = generatePassword()"><el-icon><Refresh /></el-icon></el-button>
              </template>
            </el-input>
            <span v-else style="color:#c0c4cc; font-size:13px">无需密码</span>
          </div>
        </el-form-item>
        <el-form-item label="允许下载"><el-switch v-model="editDialog.allow_download" /></el-form-item>
        <el-form-item label="有效期">
          <el-select v-model="editDialog.expireHours" style="width:100%">
            <el-option label="永久有效" :value="-1" />
            <el-option label="立即过期" :value="0" />
            <el-option label="1 小时" :value="1" />
            <el-option label="24 小时" :value="24" />
            <el-option label="7 天" :value="168" />
            <el-option label="30 天" :value="720" />
          </el-select>
        </el-form-item>
        <el-form-item label="最大访问">
          <el-input-number v-model="editDialog.max_views" :min="0" :max="99999" :step="1" />
          <span style="margin-left:8px; color:#909399; font-size:12px">0 = 不限</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="editDialog.loading" @click="saveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { shareApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import FileIcon from '@/components/FileIcon.vue'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const perm = (code: string) => userStore.hasPermission(code)

const shares = ref<any[]>([])
const loading = ref(false)
const selected = ref<any[]>([])
const pagination = reactive({ page: 1, pageSize: 10, total: 0 })
const storageNames = ref<string[]>([])
const filterStorageName = ref('')

const allChecked = computed(() => shares.value.length > 0 && shares.value.every((s: any) => s._checked))
const isIndeterminate = computed(() => {
  const checked = shares.value.filter((s: any) => s._checked).length
  return checked > 0 && checked < shares.value.length
})

function onSelectAll(val: boolean) {
  shares.value.forEach((s: any) => { s._checked = val })
  selected.value = val ? [...shares.value] : []
}
function onRowCheck(row: any, val: boolean) {
  if (val) { if (!selected.value.some(f => f.id === row.id)) selected.value.push(row) }
  else { const idx = selected.value.findIndex(f => f.id === row.id); if (idx >= 0) selected.value.splice(idx, 1) }
}
function clearSelection() { shares.value.forEach(s => s._checked = false); selected.value = [] }

async function loadStorageNames() {
  try {
    // 分批加载所有存储源名称
    const names = new Set<string>()
    let page = 1
    while (true) {
      const res: any = await shareApi.list({ page, page_size: 100 })
      ;(res.items || []).forEach((s: any) => {
        if (s.storage_name) names.add(s.storage_name)
      })
      if (res.items?.length < 100 || page * 100 >= res.total) break
      page++
    }
    storageNames.value = Array.from(names).sort()
  } catch {}
}

function onFilterChange() {
  pagination.page = 1
  loadShares()
}

async function loadShares() {
  loading.value = true
  try {
    const params: any = { page: pagination.page, page_size: pagination.pageSize }
    if (filterStorageName.value) {
      params.storage_name = filterStorageName.value
    }
    const res: any = await shareApi.list(params)
    shares.value = (res.items || []).map((s: any) => ({ ...s, _checked: false }))
    pagination.total = res.total || 0
  }
  catch {} finally { loading.value = false }
}

function getFullUrl(path: string) { return `${window.location.origin}${path}` }

async function copyUrl(row: any) {
  const url = getFullUrl(row.share_url)
  let text = `链接：${url}`
  if (row.password) text += `\n密码：${row.password}`
  try { await navigator.clipboard.writeText(text); ElMessage.success('已复制') }
  catch { const ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); ElMessage.success('已复制') }
}

function openUrl(row: any) { window.open(getFullUrl(row.share_url), '_blank') }

async function toggleShare(row: any) {
  try { await shareApi.toggle(row.id) } catch { row.enabled = !row.enabled }
}

async function deleteShare(id: number) {
  try { await shareApi.delete(id); ElMessage.success('已删除'); await loadShares() } catch {}
}

async function batchDelete() {
  if (!selected.value.length) return
  try { await ElMessageBox.confirm(`确定取消选中的 ${selected.value.length} 个分享？`, '批量取消分享', { type: 'warning' }) } catch { return }
  loading.value = true
  try {
    const ids = selected.value.map(s => s.id)
    const res: any = await shareApi.batchDelete(ids)
    ElMessage.success(`已取消 ${res.deleted} 个分享`); clearSelection(); await loadShares()
  } catch {} finally { loading.value = false }
}

const editDialog = reactive({ visible: false, id: 0, file_name: '', password: '', passwordEnabled: false, allow_download: true, expireHours: -1, max_views: 0, loading: false })

async function copyPwd(pwd: string) {
  try {
    await navigator.clipboard.writeText(pwd)
    ElMessage.success('密码已复制')
  } catch {
    ElMessage.error('复制失败')
  }
}

function generatePassword(): string {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789'
  let result = ''
  for (let i = 0; i < 6; i++) result += chars[Math.floor(Math.random() * chars.length)]
  return result
}

function openEdit(row: any) {
  editDialog.id = row.id; editDialog.file_name = row.file_name
  editDialog.password = row.password || ''; editDialog.passwordEnabled = !!row.password
  editDialog.allow_download = row.allow_download; editDialog.max_views = row.max_views || 0
  if (row.expire_at) { const diff = new Date(row.expire_at).getTime() - Date.now(); editDialog.expireHours = diff <= 0 ? 0 : Math.ceil(diff / 3600000) }
  else editDialog.expireHours = -1
  editDialog.visible = true
}

async function saveEdit() {
  editDialog.loading = true
  try {
    await shareApi.update(editDialog.id, { allow_download: editDialog.allow_download, password: editDialog.password || null, expire_hours: editDialog.expireHours !== null && editDialog.expireHours !== undefined ? editDialog.expireHours : null, max_views: editDialog.max_views || null })
    ElMessage.success('已保存'); editDialog.visible = false; await loadShares()
  } catch {} finally { editDialog.loading = false }
}

function isExpired(expireAt: string) { return new Date(expireAt).getTime() < Date.now() }
function formatExpire(expireAt: string) {
  const diff = new Date(expireAt).getTime() - Date.now()
  if (diff <= 0) return '已过期'
  const hours = Math.floor(diff / 3600000)
  if (hours < 1) return `${Math.floor(diff / 60000)}分`
  if (hours < 24) return `${hours}时`
  return `${Math.floor(hours / 24)}天`
}

onMounted(() => {
  loadShares()
  loadStorageNames()
})
</script>

<style scoped>
.shares-page {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 统计栏 */
.stats-bar {
  display: flex; gap: 12px; margin-bottom: 12px; width: 100%;
}
.stat-item {
  flex: 1; background: #fff; border-radius: 10px; padding: 14px 16px;
  display: flex; flex-direction: column; align-items: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.stat-num { font-size: 22px; font-weight: 700; color: #303133; line-height: 1; }
.stat-label { font-size: 12px; color: #909399; margin-top: 4px; }

/* 操作栏 */
.action-bar {
  display: flex; align-items: center; justify-content: flex-end; gap: 12px;
  margin-bottom: 12px; width: 100%;
}
.filter-group {
  margin-right: auto;
}
.batch-info {
  display: flex; align-items: center; gap: 10px;
  font-size: 13px; color: #606266;
  background: #fef0f0; padding: 4px 12px; border-radius: 6px;
  margin-right: auto;
}

/* 表格卡片 */
.table-card {
  background: #fff; border-radius: 10px; overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04); width: 100%;
}

/* 表格 */
.shares-table {
  width: 100%; border-collapse: collapse; font-size: 13px; table-layout: fixed;
}
.shares-table thead th {
  padding: 12px 8px; text-align: left;
  font-weight: 600; font-size: 13px; color: #909399;
  background: #fafafa; border-bottom: 1px solid #f0f0f0;
}
.shares-table tbody tr { transition: background 0.15s; }
.shares-table tbody tr:hover { background: #f5f7fa; }
.shares-table tbody td {
  padding: 12px 8px; border-bottom: 1px solid #f5f5f5;
  color: #303133; font-weight: 400; line-height: 23px; vertical-align: middle;
}
.shares-table tbody tr:last-child td { border-bottom: none; }
.row-disabled { opacity: 0.5; }

/* 单元格样式 */
.file-name {
  font-weight: 400; font-size: 13px; color: #303133;
  display: block; max-width: 100%;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.cell-muted { font-size: 13px; color: #606266; }
.link-cell { display: flex; gap: 2px; }
.action-cell { display: flex; gap: 0; white-space: nowrap; }

/* 标签 */
.tag-permanent {
  font-size: 11px; padding: 1px 6px; border-radius: 3px;
  background: #f0f9eb; color: #67c23a;
}
.tag-expired {
  font-size: 11px; padding: 1px 6px; border-radius: 3px;
  background: #fef0f0; color: #f56c6c;
}
.tag-active {
  font-size: 11px; padding: 1px 6px; border-radius: 3px;
  background: #fdf6ec; color: #e6a23c;
}
.pwd-text {
  font-size: 13px; font-family: monospace; color: #e6a23c;
  max-width: 60px; display: block;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  cursor: pointer;
}

/* 空状态 */
.empty-cell {
  text-align: center; padding: 40px 0 !important; color: #c0c4cc;
}
.empty-cell p { margin: 8px 0 0; font-size: 13px; }
</style>

<template>
  <el-card>
    <template #header>
      <div style="display: flex; align-items: center; justify-content: space-between">
        <span style="font-weight: 600; font-size: 16px">存储管理</span>
        <el-button type="primary" @click="openCreate" v-if="perm('storage.create')">
          <el-icon style="margin-right: 4px"><Plus /></el-icon>
          添加存储源
        </el-button>
      </div>
    </template>

    <el-table :data="storages" stripe style="width: 100%">
      <el-table-column prop="id" label="ID" width="60" />
      <el-table-column prop="name" label="名称" min-width="120">
        <template #default="{ row }">
          <div style="display: flex; align-items: center; gap: 8px">
            <div :style="{ width: '4px', height: '24px', borderRadius: '2px', background: row.color }"></div>
            <span style="font-weight: 600">{{ row.name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="类型" width="140">
        <template #default="{ row }">
          <el-tag>{{ typeNames[row.storage_type] || row.storage_type }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="160" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-switch v-if="perm('storage.toggle')" v-model="row.enabled" @change="toggleStorage(row)" />
          <el-tag v-else :type="row.enabled ? 'success' : 'danger'" size="small">{{ row.enabled ? '启用' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="主页显示" width="100">
        <template #default="{ row }">
          <el-switch v-if="perm('storage.edit')" v-model="row.is_public" @change="togglePublic(row)" />
          <el-tag v-else :type="row.is_public ? 'success' : 'info'" size="small">{{ row.is_public ? '公开' : '私有' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="加密规则" width="100">
        <template #default="{ row }">
          <el-button size="small" type="warning" link @click="openProtectedPaths(row)" v-if="perm('storage.edit')">
            设置
            <el-badge v-if="row.protected_paths?.length" :value="row.protected_paths.length" :max="99" style="margin-left: 4px" />
          </el-button>
          <span v-else-if="row.protected_paths?.length">{{ row.protected_paths.length }} 条</span>
          <span v-else style="color: #c0c4cc">无</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" link @click="$router.push(`/admin/files/${row.id}`)">
            浏览
          </el-button>
          <el-button size="small" type="warning" link @click="testConn(row)" v-if="perm('storage.test')">
            测试
          </el-button>
          <el-button size="small" type="info" link @click="openEdit(row)" v-if="perm('storage.edit')">
            编辑
          </el-button>
          <el-popconfirm title="确定删除?" @confirm="deleteStorage(row.id)" v-if="perm('storage.delete')">
            <template #reference>
              <el-button size="small" type="danger" link>删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑存储源' : '添加存储源'"
      width="600px"
      destroy-on-close
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="140px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="例如: 我的 OSS" />
        </el-form-item>
        <el-form-item label="存储类型" prop="storage_type" v-if="!editingId">
          <el-select v-model="form.storage_type" placeholder="选择存储类型" style="width: 100%" @change="onTypeChange">
            <el-option v-for="t in storageTypes" :key="t.type" :label="t.name" :value="t.type" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" placeholder="可选描述" />
        </el-form-item>
        <el-form-item label="颜色">
          <el-color-picker v-model="form.color" />
        </el-form-item>

        <!-- Dynamic config fields -->
        <template v-if="currentFields.length > 0">
          <el-divider content-position="left">连接配置</el-divider>
          <el-form-item
            v-for="field in currentFields"
            :key="field.key"
            :label="field.label"
            :required="field.required"
          >
            <!-- Select type field -->
            <el-select
              v-if="field.type === 'select'"
              v-model="form.config[field.key]"
              :placeholder="field.placeholder || '请选择'"
              filterable
              allow-create
              style="width: 100%"
            >
              <el-option
                v-for="opt in field.options"
                :key="opt.value"
                :label="`${opt.label} (${opt.value})`"
                :value="opt.value"
              />
            </el-select>
            <!-- Default input field -->
            <el-input
              v-else
              v-model="form.config[field.key]"
              :placeholder="field.placeholder || ''"
            />
          </el-form-item>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- Protected Paths Dialog -->
    <el-dialog
      v-model="protectedPathsVisible"
      :title="`加密规则设置 - ${protectedPathsStorage?.name || ''}`"
      width="700px"
      destroy-on-close
    >
      <div style="margin-bottom: 20px;">
        <div style="color: #606266; font-size: 14px; margin-bottom: 12px;">
          使用 Glob 表达式设置加密规则，系统按顺序匹配第一个符合的规则
        </div>
        <el-card shadow="never" style="background: #f5f7fa;">
          <div style="font-size: 13px; color: #909399; line-height: 1.8;">
            <div><strong>规则说明：</strong></div>
            <div><code>/</code> — 根路径需要密码访问</div>
            <div><code>/music/*</code> — music 文件夹需要密码，子文件夹不加密</div>
            <div><code>/music/**</code> — music 文件夹及其所有子文件夹都需要密码</div>
            <div style="margin-top: 8px; color: #e6a23c;">
              <el-icon style="vertical-align: middle;"><Warning /></el-icon>
              规则按顺序匹配，可通过拖拽调整优先级
            </div>
          </div>
        </el-card>
      </div>

      <!-- Add new rule -->
      <el-card shadow="never" style="margin-bottom: 16px;">
        <div style="display: flex; gap: 12px; align-items: flex-end;">
          <el-form-item label="匹配规则" style="flex: 1; margin-bottom: 0;">
            <el-input v-model="newRule.pattern" placeholder="例如: /music/**">
              <template #append>
                <el-tooltip content="/* 匹配一级目录，/** 匹配所有子目录" placement="top">
                  <el-icon><QuestionFilled /></el-icon>
                </el-tooltip>
              </template>
            </el-input>
          </el-form-item>
          <el-form-item label="访问密码" style="flex: 1; margin-bottom: 0;">
            <el-input v-model="newRule.password" placeholder="请输入密码" />
          </el-form-item>
          <el-button type="primary" @click="addRule">
            <el-icon style="margin-right: 4px"><Plus /></el-icon>
            添加
          </el-button>
        </div>
      </el-card>

      <!-- Rules list with drag support -->
      <div class="rules-list" v-if="rulesList.length">
        <div class="rules-header">
          <span style="font-size: 13px; color: #909399;">
            <el-icon style="vertical-align: middle;"><Sort /></el-icon>
            拖拽调整规则顺序（上方规则优先匹配）
          </span>
        </div>
        <div
          v-for="(rule, index) in rulesList"
          :key="index"
          class="rule-item"
          draggable="true"
          @dragstart="onDragStart($event, index)"
          @dragover.prevent="onDragOver($event, index)"
          @drop="onDrop($event, index)"
          @dragend="onDragEnd"
          :class="{ 'drag-over': dragOverIndex === index, 'dragging': dragIndex === index }"
        >
          <div class="rule-drag-handle">
            <el-icon><Rank /></el-icon>
          </div>
          <div class="rule-index">{{ index + 1 }}</div>
          <div class="rule-pattern">
            <code>{{ rule.pattern }}</code>
            <span class="rule-desc">{{ getPatternDesc(rule.pattern) }}</span>
          </div>
          <div class="rule-password">
            <span style="font-family: monospace; color: #e6a23c;">{{ rule.password }}</span>
          </div>
          <div class="rule-actions">
            <el-button size="small" type="danger" link @click="removeRule(index)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <el-empty v-else description="暂无加密规则" :image-size="60" />

      <template #footer>
        <el-button @click="protectedPathsVisible = false">取消</el-button>
        <el-button type="primary" @click="saveRules">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { storageApi } from '@/api'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const perm = (code: string) => userStore.hasPermission(code)

const typeNames: Record<string, string> = {
  aliyun: '阿里云 OSS',
  huawei: '华为云 OBS',
  tencent: '腾讯云 COS',
  baidu: '百度云 BOS',
  upyun: '又拍云 USS',
  qiniu: '七牛云 Kodo',
  volcengine: '火山引擎 TOS',
  local: '本地文件',
}

const storages = ref<any[]>([])
const storageTypes = ref<any[]>([])
const dialogVisible = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const formRef = ref()

const form = reactive({
  name: '',
  storage_type: '',
  description: '',
  color: '#409EFF',
  config: {} as Record<string, string>,
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  storage_type: [{ required: true, message: '请选择存储类型', trigger: 'change' }],
}

const currentFields = ref<any[]>([])

function onTypeChange(type: string) {
  const st = storageTypes.value.find(t => t.type === type)
  currentFields.value = st?.fields || []
  form.config = {}
}

async function loadData() {
  storages.value = await storageApi.list() as any
  storageTypes.value = await storageApi.getTypes() as any
}

function openCreate() {
  editingId.value = null
  form.name = ''
  form.storage_type = ''
  form.description = ''
  form.color = '#409EFF'
  form.config = {}
  currentFields.value = []
  dialogVisible.value = true
}

async function openEdit(row: any) {
  editingId.value = row.id
  form.name = row.name
  form.storage_type = row.storage_type
  form.description = row.description || ''
  form.color = row.color || '#409EFF'
  // Load full config (without masking)
  try {
    const full: any = await storageApi.get(row.id)
    form.config = full.config || {}
  } catch {
    form.config = row.config || {}
  }
  const st = storageTypes.value.find(t => t.type === row.storage_type)
  currentFields.value = st?.fields || []
  dialogVisible.value = true
}

async function handleSave() {
  try {
    await formRef.value?.validate()
  } catch { return }

  saving.value = true
  try {
    if (editingId.value) {
      await storageApi.update(editingId.value, {
        name: form.name,
        description: form.description,
        color: form.color,
        config: form.config,
      })
      ElMessage.success('更新成功')
    } else {
      await storageApi.create({
        name: form.name,
        storage_type: form.storage_type,
        description: form.description,
        color: form.color,
        config: form.config,
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

async function deleteStorage(id: number) {
  try {
    await storageApi.delete(id)
    ElMessage.success('已删除')
    await loadData()
  } catch {}
}

async function toggleStorage(row: any) {
  try {
    await storageApi.toggle(row.id)
    ElMessage.success(row.enabled ? '已启用' : '已禁用')
  } catch {
    row.enabled = !row.enabled
  }
}

async function togglePublic(row: any) {
  try {
    await storageApi.update(row.id, { is_public: row.is_public })
    ElMessage.success(row.is_public ? '已设置为主页显示' : '已取消主页显示')
  } catch {
    row.is_public = !row.is_public
  }
}

// Protected Paths Dialog
const protectedPathsVisible = ref(false)
const protectedPathsStorage = ref<any>(null)
const rulesList = ref<any[]>([])
const newRule = reactive({ pattern: '', password: '' })

// Drag state
const dragIndex = ref<number | null>(null)
const dragOverIndex = ref<number | null>(null)

function openProtectedPaths(row: any) {
  protectedPathsStorage.value = row
  rulesList.value = row.protected_paths ? [...row.protected_paths] : []
  newRule.pattern = ''
  newRule.password = ''
  protectedPathsVisible.value = true
}

function getPatternDesc(pattern: string): string {
  if (pattern === '/') return '根目录'
  if (pattern.endsWith('/**')) return '目录及所有子目录'
  if (pattern.endsWith('/*')) return '仅一级目录'
  return '精确匹配'
}

function addRule() {
  if (!newRule.pattern || !newRule.password) {
    ElMessage.warning('请输入匹配规则和密码')
    return
  }
  // 验证规则格式
  const pattern = newRule.pattern.trim()
  if (!pattern.startsWith('/')) {
    ElMessage.warning('规则必须以 / 开头')
    return
  }
  // 检查是否已存在
  const exists = rulesList.value.some(r => r.pattern === pattern)
  if (exists) {
    ElMessage.warning('该规则已存在')
    return
  }
  rulesList.value.push({
    pattern: pattern,
    password: newRule.password,
  })
  newRule.pattern = ''
  newRule.password = ''
}

function removeRule(index: number) {
  rulesList.value.splice(index, 1)
}

// Drag handlers
function onDragStart(event: DragEvent, index: number) {
  dragIndex.value = index
  event.dataTransfer!.effectAllowed = 'move'
  // Add dragging class after a small delay
  setTimeout(() => {
    const el = event.target as HTMLElement
    el.classList.add('dragging')
  }, 0)
}

function onDragOver(event: DragEvent, index: number) {
  event.preventDefault()
  dragOverIndex.value = index
}

function onDrop(event: DragEvent, targetIndex: number) {
  event.preventDefault()
  if (dragIndex.value === null || dragIndex.value === targetIndex) return
  
  const item = rulesList.value[dragIndex.value]
  rulesList.value.splice(dragIndex.value, 1)
  rulesList.value.splice(targetIndex, 0, item)
  
  dragIndex.value = null
  dragOverIndex.value = null
}

function onDragEnd() {
  dragIndex.value = null
  dragOverIndex.value = null
}

async function saveRules() {
  try {
    await storageApi.update(protectedPathsStorage.value.id, {
      protected_paths: rulesList.value,
    })
    protectedPathsStorage.value.protected_paths = [...rulesList.value]
    protectedPathsVisible.value = false
    ElMessage.success('加密规则已保存')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '保存失败')
  }
}

async function testConn(row: any) {
  try {
    const res: any = await storageApi.testConnection(row.id)
    if (res.success) {
      ElMessage.success(res.message || '连接成功')
    } else {
      ElMessage.warning(res.message || '连接失败')
    }
  } catch {}
}

onMounted(loadData)
</script>

<style scoped>
.rules-list {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  overflow: hidden;
}

.rules-header {
  padding: 12px 16px;
  background: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
}

.rule-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  cursor: grab;
  transition: all 0.2s ease;
}

.rule-item:last-child {
  border-bottom: none;
}

.rule-item:hover {
  background: #f5f7fa;
}

.rule-item.dragging {
  opacity: 0.5;
  background: #ecf5ff;
}

.rule-item.drag-over {
  border-top: 2px solid #409eff;
}

.rule-drag-handle {
  color: #c0c4cc;
  cursor: grab;
}

.rule-drag-handle:active {
  cursor: grabbing;
}

.rule-index {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.rule-pattern {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.rule-pattern code {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 14px;
  color: #303133;
  background: #f5f7fa;
  padding: 2px 8px;
  border-radius: 4px;
}

.rule-desc {
  font-size: 12px;
  color: #909399;
}

.rule-password {
  min-width: 80px;
}

.rule-actions {
  flex-shrink: 0;
}
</style>
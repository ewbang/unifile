<template>
  <div class="users-page">
    <el-card style="margin-bottom:12px">
      <div style="display:flex; align-items:center; justify-content:space-between">
        <span style="font-weight:600; font-size:16px">用户管理</span>
        <el-button type="primary" size="small" @click="openCreate"><el-icon style="margin-right:4px"><Plus /></el-icon>添加用户</el-button>
      </div>
    </el-card>

    <el-card v-loading="loading">
      <el-table :data="users" stripe style="width:100%" empty-text="暂无用户">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="用户名" min-width="120">
          <template #default="{ row }">
            <div style="display:flex; align-items:center; gap:6px">
              <el-avatar :size="28" style="background:#409EFF; font-size:12px">{{ row.username[0]?.toUpperCase() }}</el-avatar>
              <span style="font-weight:600">{{ row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="row.role_code === 'admin' ? 'danger' : row.role_code === 'user' ? '' : 'info'" size="small">
              {{ row.role_name || '未知' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">{{ row.enabled ? '正常' : '停用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">{{ row.created_at?.replace('T', ' ').slice(0, 16) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="warning" link @click="openResetPwd(row)">重置密码</el-button>
            <el-popconfirm v-if="row.id !== currentUserId" title="确定删除此用户?" @confirm="deleteUser(row.id)">
              <template #reference><el-button size="small" type="danger" link>删除</el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑用户' : '添加用户'" width="450px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="用户名"><el-input v-model="dialog.username" /></el-form-item>
        <el-form-item v-if="!dialog.isEdit" label="密码"><el-input v-model="dialog.password" type="password" show-password /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="dialog.role_id" style="width:100%">
            <el-option v-for="r in roles" :key="r.id" :label="r.name" :value="r.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用"><el-switch v-model="dialog.enabled" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.loading" @click="saveUser">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="pwdDialog.visible" title="重置密码" width="400px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="用户">{{ pwdDialog.username }}</el-form-item>
        <el-form-item label="新密码"><el-input v-model="pwdDialog.password" type="password" show-password /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="pwdDialog.loading" @click="resetPassword">确认重置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { usersApi, rolesApi } from '@/api'
import { ElMessage } from 'element-plus'

const users = ref<any[]>([])
const roles = ref<any[]>([])
const loading = ref(false)
const currentUserId = ref(0)

const dialog = reactive({
  visible: false, isEdit: false, loading: false,
  id: 0, username: '', password: '', role_id: 2, enabled: true,
})

const pwdDialog = reactive({ visible: false, loading: false, id: 0, username: '', password: '' })

async function loadUsers() {
  loading.value = true
  try { users.value = await usersApi.list() } catch {} finally { loading.value = false }
}

async function loadRoles() {
  try { roles.value = await rolesApi.list() } catch {}
}

async function loadCurrentUser() {
  try { const me: any = await usersApi.getMe(); currentUserId.value = me.id } catch {}
}

function openCreate() {
  dialog.isEdit = false; dialog.id = 0; dialog.username = ''; dialog.password = ''; dialog.role_id = 2; dialog.enabled = true; dialog.visible = true
}

function openEdit(row: any) {
  dialog.isEdit = true; dialog.id = row.id; dialog.username = row.username; dialog.password = ''
  dialog.role_id = row.role_id; dialog.enabled = row.enabled; dialog.visible = true
}

async function saveUser() {
  dialog.loading = true
  try {
    if (dialog.isEdit) {
      await usersApi.update(dialog.id, { username: dialog.username, role_id: dialog.role_id, enabled: dialog.enabled })
    } else {
      await usersApi.create({ username: dialog.username, password: dialog.password, role_id: dialog.role_id })
    }
    ElMessage.success('已保存'); dialog.visible = false; await loadUsers()
  } catch {} finally { dialog.loading = false }
}

async function deleteUser(id: number) {
  try { await usersApi.delete(id); ElMessage.success('已删除'); await loadUsers() } catch {}
}

function openResetPwd(row: any) {
  pwdDialog.id = row.id; pwdDialog.username = row.username; pwdDialog.password = ''; pwdDialog.visible = true
}

async function resetPassword() {
  if (!pwdDialog.password) { ElMessage.warning('请输入新密码'); return }
  pwdDialog.loading = true
  try {
    await usersApi.update(pwdDialog.id, { password: pwdDialog.password })
    ElMessage.success('密码已重置'); pwdDialog.visible = false
  } catch {} finally { pwdDialog.loading = false }
}

onMounted(() => { loadUsers(); loadRoles(); loadCurrentUser() })
</script>

<style scoped>
.users-page { max-width: 1200px; margin: 0 auto; }
</style>

<template>
  <div>
    <el-card style="margin-bottom:12px">
      <div style="display:flex; align-items:center; justify-content:space-between">
        <span style="font-weight:600; font-size:16px">角色管理</span>
        <el-button type="primary" size="small" @click="openCreate" v-if="perm('role_manage')"><el-icon style="margin-right:4px"><Plus /></el-icon>添加角色</el-button>
      </div>
    </el-card>

    <el-card v-loading="loading">
      <el-table :data="roles" stripe style="width:100%" empty-text="暂无角色">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="name" label="角色名称" width="120">
          <template #default="{ row }">
            <el-tag :type="row.code === 'admin' ? 'danger' : row.code === 'user' ? '' : 'info'">{{ row.name }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="code" label="角色编码" width="120" />
        <el-table-column prop="description" label="描述" min-width="200" />
        <el-table-column label="权限数量" width="100">
          <template #default="{ row }">{{ row.menu_ids?.length || 0 }} 项</template>
        </el-table-column>
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_system" type="warning" size="small">系统</el-tag>
            <el-tag v-else size="small" type="info">自定义</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openEdit(row)" v-if="perm('role_manage')">编辑权限</el-button>
            <el-popconfirm v-if="!row.is_system && perm('role_manage')" title="确定删除?" @confirm="deleteRole(row.id)">
              <template #reference><el-button size="small" type="danger" link>删除</el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑弹窗 -->
    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑角色权限' : '添加角色'" width="600px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="角色名称"><el-input v-model="dialog.name" /></el-form-item>
        <el-form-item label="角色编码"><el-input v-model="dialog.code" :disabled="dialog.isEdit" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="dialog.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="菜单权限">
          <div style="max-height:400px; overflow-y:auto; width:100%">
            <div v-for="menu in menuTree" :key="menu.id" style="margin-bottom:8px">
              <el-checkbox :model-value="isMenuChecked(menu.id)" :indeterminate="isMenuIndeterminate(menu.id)" @change="(val: boolean) => toggleMenu(menu.id, val)">
                <span style="font-weight:600">{{ menu.name }}</span>
                <span style="color:#909399; font-size:12px; margin-left:4px">({{ menu.permission_code }})</span>
              </el-checkbox>
              <div v-if="menu.children?.length" style="margin-left:24px; margin-top:4px">
                <el-checkbox v-for="btn in menu.children" :key="btn.id" :model-value="dialog.menu_ids.includes(btn.id)" @change="(val: boolean) => toggleMenu(btn.id, val)">
                  {{ btn.name }}
                  <span style="color:#c0c4cc; font-size:11px; margin-left:2px">{{ btn.permission_code }}</span>
                </el-checkbox>
              </div>
            </div>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.loading" @click="saveRole">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { rolesApi } from '@/api'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const perm = (code: string) => userStore.hasPermission(code)

const roles = ref<any[]>([])
const allMenus = ref<any[]>([])
const loading = ref(false)

const dialog = reactive({
  visible: false, isEdit: false, loading: false,
  id: 0, name: '', code: '', description: '', menu_ids: [] as number[],
})

const menuTree = computed(() => {
  const parents = allMenus.value.filter(m => m.parent_id === 0).sort((a, b) => a.sort_order - b.sort_order)
  return parents.map(p => ({
    ...p,
    children: allMenus.value.filter(m => m.parent_id === p.id).sort((a, b) => a.sort_order - b.sort_order),
  }))
})

function isMenuChecked(parentId: number) {
  const parent = allMenus.value.find(m => m.id === parentId)
  const children = allMenus.value.filter(m => m.parent_id === parentId)
  if (!children.length) return dialog.menu_ids.includes(parentId)
  return children.every(c => dialog.menu_ids.includes(c.id)) && dialog.menu_ids.includes(parentId)
}

function isMenuIndeterminate(parentId: number) {
  const children = allMenus.value.filter(m => m.parent_id === parentId)
  if (!children.length) return false
  const checked = children.filter(c => dialog.menu_ids.includes(c.id)).length
  return checked > 0 && checked < children.length
}

function toggleMenu(id: number, val: boolean) {
  const children = allMenus.value.filter(m => m.parent_id === id)
  if (val) {
    if (!dialog.menu_ids.includes(id)) dialog.menu_ids.push(id)
    // 勾选父菜单时自动勾选所有子菜单
    children.forEach(c => { if (!dialog.menu_ids.includes(c.id)) dialog.menu_ids.push(c.id) })
  } else {
    dialog.menu_ids = dialog.menu_ids.filter(i => i !== id)
    children.forEach(c => { dialog.menu_ids = dialog.menu_ids.filter(i => i !== c.id) })
  }
}

async function loadRoles() {
  loading.value = true
  try { roles.value = await rolesApi.list() } catch {} finally { loading.value = false }
}

async function loadMenus() {
  try { allMenus.value = await rolesApi.getMenus() } catch {}
}

function openCreate() {
  dialog.isEdit = false; dialog.id = 0; dialog.name = ''; dialog.code = ''; dialog.description = ''
  dialog.menu_ids = []; dialog.visible = true
}

function openEdit(row: any) {
  dialog.isEdit = true; dialog.id = row.id; dialog.name = row.name; dialog.code = row.code
  dialog.description = row.description || ''; dialog.menu_ids = [...(row.menu_ids || [])]
  dialog.visible = true
}

async function saveRole() {
  dialog.loading = true
  try {
    if (dialog.isEdit) {
      await rolesApi.update(dialog.id, { name: dialog.name, description: dialog.description, menu_ids: dialog.menu_ids })
    } else {
      await rolesApi.create({ name: dialog.name, code: dialog.code, description: dialog.description, menu_ids: dialog.menu_ids })
    }
    ElMessage.success('已保存'); dialog.visible = false; await loadRoles()
  } catch {} finally { dialog.loading = false }
}

async function deleteRole(id: number) {
  try { await rolesApi.delete(id); ElMessage.success('已删除'); await loadRoles() } catch {}
}

onMounted(() => { loadRoles(); loadMenus() })
</script>

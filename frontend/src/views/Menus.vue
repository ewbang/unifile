<template>
  <div>
    <el-card style="margin-bottom:12px">
      <div style="display:flex; align-items:center; justify-content:space-between">
        <span style="font-weight:600; font-size:16px">菜单管理</span>
        <el-button type="primary" size="small" @click="openCreate()" v-if="perm('menu_manage')"><el-icon style="margin-right:4px"><Plus /></el-icon>添加菜单</el-button>
      </div>
    </el-card>

    <el-card v-loading="loading">
      <el-table :data="menuTree" stripe style="width:100%" row-key="id" default-expand-all :tree-props="{ children: 'children' }">
        <el-table-column prop="name" label="菜单名称" min-width="200">
          <template #default="{ row }">
            <el-icon v-if="row.icon" style="margin-right:4px"><component :is="row.icon" /></el-icon>
            <span>{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="permission_code" label="权限标识" width="200">
          <template #default="{ row }"><code style="font-size:12px; color:#909399">{{ row.permission_code }}</code></template>
        </el-table-column>
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.menu_type === 'menu' ? '' : 'warning'" size="small">{{ row.menu_type === 'menu' ? '菜单' : '按钮' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路由" width="160">
          <template #default="{ row }"><span style="font-size:12px">{{ row.path || '-' }}</span></template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="60" />
        <el-table-column label="显示" width="60">
          <template #default="{ row }"><el-tag v-if="row.visible" type="success" size="small">是</el-tag><el-tag v-else type="info" size="small">否</el-tag></template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="openEdit(row)" v-if="perm('menu_manage')">编辑</el-button>
            <el-button size="small" type="success" link @click="openCreate(row.id)" v-if="perm('menu_manage')">子项</el-button>
            <el-popconfirm title="确定删除?" @confirm="deleteMenu(row.id)" v-if="perm('menu_manage')">
              <template #reference><el-button size="small" type="danger" link>删除</el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialog.visible" :title="dialog.isEdit ? '编辑菜单' : '添加菜单'" width="500px" destroy-on-close>
      <el-form label-width="90px">
        <el-form-item label="菜单名称"><el-input v-model="dialog.name" /></el-form-item>
        <el-form-item label="权限标识"><el-input v-model="dialog.permission_code" placeholder="如 file.mkdir" /></el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="dialog.menu_type">
            <el-radio value="menu">菜单</el-radio>
            <el-radio value="button">按钮</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="路由路径" v-if="dialog.menu_type === 'menu'"><el-input v-model="dialog.path" placeholder="/dashboard" /></el-form-item>
        <el-form-item label="图标" v-if="dialog.menu_type === 'menu'"><el-input v-model="dialog.icon" placeholder="Odometer" /></el-form-item>
        <el-form-item label="排序"><el-input-number v-model="dialog.sort_order" :min="0" /></el-form-item>
        <el-form-item label="是否显示"><el-switch v-model="dialog.visible" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.loading" @click="saveMenu">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { menusApi } from '@/api'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const perm = (code: string) => userStore.hasPermission(code)

const menus = ref<any[]>([])
const loading = ref(false)

const dialog = reactive({
  visible: false, isEdit: false, loading: false,
  id: 0, parent_id: 0, name: '', menu_type: 'menu', permission_code: '',
  path: '', icon: '', sort_order: 0, visible: true,
})

const menuTree = computed(() => {
  const parents = menus.value.filter(m => m.parent_id === 0).sort((a, b) => a.sort_order - b.sort_order)
  return parents.map(p => ({
    ...p,
    children: menus.value.filter(m => m.parent_id === p.id).sort((a, b) => a.sort_order - b.sort_order),
  }))
})

async function loadMenus() {
  loading.value = true
  try { menus.value = await menusApi.list() } catch {} finally { loading.value = false }
}

function openCreate(parentId = 0) {
  dialog.isEdit = false; dialog.id = 0; dialog.parent_id = parentId
  dialog.name = ''; dialog.menu_type = parentId ? 'button' : 'menu'
  dialog.permission_code = ''; dialog.path = ''; dialog.icon = ''
  dialog.sort_order = 0; dialog.visible = true; dialog.visible = true
}

function openEdit(row: any) {
  dialog.isEdit = true; dialog.id = row.id; dialog.parent_id = row.parent_id
  dialog.name = row.name; dialog.menu_type = row.menu_type; dialog.permission_code = row.permission_code
  dialog.path = row.path || ''; dialog.icon = row.icon || ''
  dialog.sort_order = row.sort_order; dialog.visible = row.visible; dialog.visible = true
}

async function saveMenu() {
  dialog.loading = true
  try {
    const data = { parent_id: dialog.parent_id, name: dialog.name, menu_type: dialog.menu_type, permission_code: dialog.permission_code, path: dialog.path, icon: dialog.icon, sort_order: dialog.sort_order, visible: dialog.visible }
    if (dialog.isEdit) await menusApi.update(dialog.id, data)
    else await menusApi.create(data)
    ElMessage.success('已保存'); dialog.visible = false; await loadMenus()
  } catch {} finally { dialog.loading = false }
}

async function deleteMenu(id: number) {
  try { await menusApi.delete(id); ElMessage.success('已删除'); await loadMenus() } catch {}
}

onMounted(loadMenus)
</script>

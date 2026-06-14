<template>
  <div
    @click="closeContextMenu"
    @contextmenu.prevent="onBlankContextMenu"
    @dragover.prevent="onDragOver"
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop"
    class="file-page"
    :class="{ 'file-page--dragging': isDragging }"
  >
    <!-- 拖拽遮罩 -->
    <transition name="el-fade-in">
      <div v-if="isDragging" class="drag-overlay">
        <el-icon :size="64" color="#409EFF"><Upload /></el-icon>
        <div style="font-size: 18px; color: #409EFF; margin-top: 12px; font-weight: 600">松开鼠标上传文件</div>
      </div>
    </transition>

    <!-- Header: breadcrumb + actions -->
    <el-card style="margin-bottom: 12px">
      <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px">
        <!-- Breadcrumb -->
        <div style="display: flex; align-items: center; gap: 4px; flex-wrap: wrap">
          <el-button text size="small" @click="goTo('/')">
            <el-icon><HomeFilled /></el-icon>
          </el-button>
          <template v-for="(crumb, idx) in breadcrumbs" :key="idx">
            <span style="color: #c0c4cc">/</span>
            <el-button text size="small" @click="goTo(crumb.path)">{{ crumb.name }}</el-button>
          </template>
        </div>

        <!-- Actions -->
        <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索文件..."
            prefix-icon="Search"
            clearable
            style="width: 180px"
            @keyup.enter="doSearch"
            @clear="clearSearch"
          />
          <el-button-group>
            <el-button :type="viewMode === 'table' ? 'primary' : ''" @click="viewMode = 'table'" size="small">
              <el-icon><List /></el-icon>
            </el-button>
            <el-button :type="viewMode === 'grid' ? 'primary' : ''" @click="viewMode = 'grid'" size="small">
              <el-icon><Grid /></el-icon>
            </el-button>
          </el-button-group>
          <el-button size="small" @click="refresh"><el-icon style="margin-right:4px"><Refresh /></el-icon>刷新</el-button>
          <el-button v-if="perm('file.mkdir')" type="primary" size="small" @click="showMkdir"><el-icon style="margin-right:4px"><FolderAdd /></el-icon>新建</el-button>
          <el-dropdown v-if="perm('file.upload')" @command="handleUploadCommand" style="margin-left:0">
            <el-button type="success" size="small"><el-icon style="margin-right:4px"><Upload /></el-icon>上传</el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="file"><el-icon><Document /></el-icon>选择文件</el-dropdown-item>
                <el-dropdown-item command="folder"><el-icon><FolderOpened /></el-icon>选择文件夹</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>

      <!-- 批量操作栏 -->
      <transition name="el-zoom-in-top">
        <div v-if="selectedFiles.length > 0" class="batch-bar">
          <span>已选 <b>{{ selectedFiles.length }}</b> 项</span>
          <el-button text size="small" @click="clearSelection">取消选择</el-button>
          <el-button v-if="perm('file.create_share')" type="success" size="small" @click="batchShare">
            <el-icon style="margin-right:4px"><Share /></el-icon>批量分享
          </el-button>
          <el-button v-if="perm('file.move')" type="warning" size="small" @click="batchMove">
            <el-icon style="margin-right:4px"><Rank /></el-icon>批量移动
          </el-button>
          <el-button v-if="perm('file.delete')" type="danger" size="small" @click="batchDelete">
            <el-icon style="margin-right:4px"><Delete /></el-icon>批量删除
          </el-button>
        </div>
      </transition>

      <!-- 上传进度 -->
      <transition name="el-zoom-in-top">
        <div v-if="uploadState.uploading" class="upload-progress-bar">
          <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px">
            <span style="font-size:13px; color:#606266; font-weight:600">
              {{ uploadState.done }}/{{ uploadState.total }} 个文件已完成
            </span>
            <span style="font-size:12px; color:#909399">总进度 {{ uploadState.totalPercent }}%</span>
          </div>
          <el-progress :percentage="uploadState.totalPercent" :show-text="false" :stroke-width="8" style="margin-bottom:10px" />
          <!-- 当前文件详情 -->
          <div v-if="uploadState.currentName" style="display:flex; align-items:center; gap:12px; font-size:12px; color:#909399">
            <span style="flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#606266">
              <el-icon style="vertical-align:middle; margin-right:4px"><Upload /></el-icon>{{ uploadState.currentName }}
            </span>
            <span>{{ uploadState.filePercent }}%</span>
            <span style="min-width:70px; text-align:right; color:#67C23A; font-weight:600">{{ uploadState.speed }}</span>
          </div>
          <el-progress v-if="uploadState.currentName" :percentage="uploadState.filePercent" :show-text="false" :stroke-width="4" :color="'#67C23A'" style="margin-top:4px" />
        </div>
      </transition>

      <!-- Search results indicator -->
      <div v-if="isSearching" style="margin-top:8px; padding:8px 12px; background:#f0f9ff; border-radius:4px; font-size:13px">
        搜索 "{{ searchKeyword }}" 找到 {{ files.length }} 个结果
        <el-button text type="primary" size="small" @click="clearSearch" style="margin-left:8px">返回</el-button>
      </div>
    </el-card>

    <!-- File list -->
    <el-card v-loading="loading">
      <!-- Table view -->
      <el-table
        v-if="viewMode === 'table'"
        ref="tableRef"
        :data="files"
        style="width:100%"
        @row-dblclick="handleDblClick"
        @row-contextmenu="onRowContextMenu"
        @selection-change="onSelectionChange"
        empty-text="空目录"
        highlight-current-row
      >
        <el-table-column type="selection" width="40" />
        <el-table-column label="名称" min-width="280">
          <template #default="{ row }">
            <div style="display:flex; align-items:center; gap:8px; cursor:pointer">
              <FileIcon :name="row.name" :is-dir="row.is_dir" :size="20" />
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="大小" width="110">
          <template #default="{ row }">
            <span v-if="!row.is_dir">{{ formatSize(row.size) }}</span>
            <span v-else-if="dirSizeLoading[row.path]" style="color:#c0c4cc">计算中...</span>
            <span v-else-if="dirSizeCache[row.path] !== undefined">{{ formatSize(dirSizeCache[row.path]) }}</span>
            <span v-else style="color:#c0c4cc; cursor:pointer" @mouseenter="loadDirSize(row.path)" @click="loadDirSize(row.path)">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_modified" label="修改时间" width="170" />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="{ row }">
            <el-button v-if="perm('file.preview')" size="small" type="primary" link @click.stop="openFile(row)">{{ row.is_dir ? '打开' : '预览' }}</el-button>
            <el-button v-if="perm('file.create_share')" size="small" type="success" link @click.stop="showShareDialog(row)">分享</el-button>
            <el-button v-if="!row.is_dir && perm('file.direct_link')" size="small" type="warning" link @click.stop="copyDirectLink(row)">直链</el-button>
            <el-button v-if="perm('file.rename')" size="small" type="info" link @click.stop="renameItem(row)">重命名</el-button>
            <el-popconfirm v-if="perm('file.delete')" title="确定删除?" @confirm="deleteItem(row)">
              <template #reference><el-button size="small" type="danger" link @click.stop>删除</el-button></template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- Grid view -->
      <div v-else class="file-grid">
        <div
          v-for="file in files"
          :key="file.path"
          class="file-grid-item"
          :class="{ 'file-grid-item--selected': isFileSelected(file) }"
          @click.exact="onGridClick(file)"
          @click.ctrl="toggleGridSelect(file)"
          @dblclick="handleDblClick(file)"
          @contextmenu.prevent.stop="onRowContextMenu(file, $event)"
        >
          <el-checkbox
            v-model="file._checked"
            class="file-grid-check"
            @click.stop
            @change="onGridCheckChange(file, $event)"
          />
          <FileIcon :name="file.name" :is-dir="file.is_dir" :size="44" />
          <div class="file-grid-name">{{ file.name }}</div>
          <div style="font-size:11px; color:#909399">
            <template v-if="!file.is_dir">{{ formatSize(file.size) }}</template>
            <template v-else-if="dirSizeLoading[file.path]">计算中...</template>
            <template v-else-if="dirSizeCache[file.path] !== undefined">{{ formatSize(dirSizeCache[file.path]) }}</template>
            <template v-else @mouseenter="loadDirSize(file.path)">—</template>
          </div>
        </div>
        <el-empty v-if="files.length === 0" description="空目录" />
      </div>
    </el-card>

    <!-- ====== 右键菜单 ====== -->
    <transition name="el-zoom-in-top">
      <div v-show="contextMenu.visible" class="context-menu" :style="{ left: contextMenu.x+'px', top: contextMenu.y+'px' }">
        <template v-if="contextMenu.target">
          <div v-if="perm('file.preview')" class="ctx-item" @click="openFile(contextMenu.target)"><el-icon><View /></el-icon><span>打开</span></div>
          <div class="ctx-item" @click="openInNewTab(contextMenu.target)"><el-icon><CopyDocument /></el-icon><span>新标签打开</span></div>
          <div class="ctx-divider"></div>
          <div v-if="perm('file.create_share')" class="ctx-item" @click="showShareDialog(contextMenu.target)"><el-icon><Share /></el-icon><span>创建分享</span></div>
          <div v-if="!contextMenu.target.is_dir && perm('file.direct_link')" class="ctx-item" @click="copyDirectLink(contextMenu.target)"><el-icon><Link /></el-icon><span>复制直链</span></div>
          <div v-if="perm('file.copy_link')" class="ctx-item" @click="copyDownloadLink(contextMenu.target)"><el-icon><CopyDocument /></el-icon><span>复制下载链接</span></div>
          <div class="ctx-divider"></div>
          <div v-if="perm('file.rename')" class="ctx-item" @click="renameItem(contextMenu.target)"><el-icon><Edit /></el-icon><span>重命名</span></div>
          <div v-if="perm('file.move')" class="ctx-item" @click="showMoveDialog(contextMenu.target)"><el-icon><Rank /></el-icon><span>移动</span></div>
          <div v-if="perm('file.copy')" class="ctx-item" @click="showCopyDialog(contextMenu.target)"><el-icon><CopyDocument /></el-icon><span>复制</span></div>
          <div v-if="!contextMenu.target.is_dir && perm('file.download')" class="ctx-item" @click="downloadFile(contextMenu.target)"><el-icon><Download /></el-icon><span>下载</span></div>
          <div class="ctx-divider"></div>
          <div v-if="perm('file.delete')" class="ctx-item ctx-item--danger" @click="deleteItem(contextMenu.target)"><el-icon><Delete /></el-icon><span>删除</span></div>
        </template>
        <template v-else>
          <div class="ctx-item" @click="refresh"><el-icon><Refresh /></el-icon><span>刷新</span></div>
          <div class="ctx-divider"></div>
          <div v-if="perm('file.mkdir')" class="ctx-item" @click="showMkdir"><el-icon><FolderAdd /></el-icon><span>新建文件夹</span></div>
          <div v-if="perm('file.upload')" class="ctx-item" @click="triggerUploadFile"><el-icon><Upload /></el-icon><span>上传文件</span></div>
          <div v-if="perm('file.upload')" class="ctx-item" @click="triggerUploadFolder"><el-icon><FolderOpened /></el-icon><span>上传文件夹</span></div>
        </template>
      </div>
    </transition>

    <!-- 隐藏的上传控件 -->
    <input ref="uploadFileInput" type="file" multiple style="display:none" @change="onUploadFiles" />
    <input ref="uploadFolderInput" type="file" webkitdirectory style="display:none" @change="onUploadFiles" />

    <!-- ====== 移动/复制对话框 ====== -->
    <el-dialog v-model="moveDialog.visible" :title="moveDialog.title" width="520px" destroy-on-close>
      <!-- 文件信息 -->
      <div class="move-file-info">
        <div class="move-file-icon">
          <el-icon :size="20" color="#fff">
            <Rank v-if="moveDialog.action === 'move'" /><CopyDocument v-else />
          </el-icon>
        </div>
        <div>
          <template v-if="moveDialog.files.length === 1">
            <span class="move-file-name">{{ moveDialog.files[0]?.name }}</span>
          </template>
          <template v-else>
            <span class="move-file-name">{{ moveDialog.files.length }} 个文件</span>
          </template>
        </div>
      </div>

      <!-- 目标路径 -->
      <div class="move-section-label">选择目标目录</div>
      <div class="dir-tree-box">
        <el-tree
          :data="moveDialog.dirTree"
          :props="{ label: 'name', children: 'children', isLeaf: 'leaf' }"
          node-key="path"
          lazy
          :load="loadTreeChildren"
          highlight-current
          @current-change="(data: any) => moveDialog.targetPath = data.path"
        >
          <template #default="{ data }">
            <div style="display:flex; align-items:center; gap:6px; padding:2px 0">
              <el-icon :size="15" color="#E6A23C"><Folder /></el-icon>
              <span>{{ data.name }}</span>
            </div>
          </template>
        </el-tree>
      </div>

      <!-- 新建文件夹 -->
      <div class="move-section-label" style="margin-top:12px">或创建新文件夹</div>
      <el-input v-model="moveDialog.newFolderName" placeholder="输入文件夹名称" size="small">
        <template #append><el-button @click="createAndSelectFolder"><el-icon><FolderAdd /></el-icon> 创建</el-button></template>
      </el-input>

      <!-- 当前选中 -->
      <div v-if="moveDialog.targetPath" class="move-target-display">
        <el-icon><FolderOpened /></el-icon>
        <span>{{ moveDialog.targetPath === '/' ? '根目录' : moveDialog.targetPath }}</span>
      </div>

      <template #footer>
        <el-button @click="moveDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="moveDialog.loading" @click="executeMoveCopy">
          {{ moveDialog.action === 'move' ? '移动到此' : '复制到此' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- ====== 分享对话框 ====== -->
    <el-dialog v-model="shareDialog.visible" :title="shareDialog.result ? '分享创建成功' : '创建分享'" width="500px" destroy-on-close>
      <el-form v-if="!shareDialog.result" label-width="100px">
        <el-form-item label="文件">
          <div v-if="shareDialog.files.length === 1">{{ shareDialog.files[0]?.name }}</div>
          <div v-else style="max-height:120px; overflow-y:auto; width:100%">
            <div v-for="(f, i) in shareDialog.files" :key="i" style="font-size:13px; padding:2px 0; color:#606266; display:flex; align-items:center; gap:4px">
              <FileIcon :name="f.name" :is-dir="f.is_dir" :size="14" />{{ f.name }}
            </div>
          </div>
        </el-form-item>
        <el-form-item label="访问密码">
          <div style="display:flex; align-items:center; gap:12px; width:100%">
            <el-switch v-model="shareDialog.passwordEnabled" @change="(val: boolean) => { if (!val) shareDialog.password = '' }" />
            <el-input v-if="shareDialog.passwordEnabled" v-model="shareDialog.password" placeholder="请输入密码" clearable style="flex:1">
              <template #append>
                <el-button @click="shareDialog.password = generatePassword()">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </template>
            </el-input>
            <span v-else style="color:#c0c4cc; font-size:13px">无需密码</span>
          </div>
        </el-form-item>
        <el-form-item label="允许下载"><el-switch v-model="shareDialog.allowDownload" /></el-form-item>
        <el-form-item label="有效期">
          <el-select v-model="shareDialog.expireHours" style="width:100%">
            <el-option label="永久有效" :value="-1" />
            <el-option label="1 小时" :value="1" />
            <el-option label="24 小时" :value="24" />
            <el-option label="7 天" :value="168" />
            <el-option label="30 天" :value="720" />
          </el-select>
        </el-form-item>
        <el-form-item label="最大访问">
          <el-input-number v-model="shareDialog.maxViews" :min="0" :max="99999" :step="1" />
          <span style="margin-left:8px; color:#909399; font-size:12px">0 = 不限</span>
        </el-form-item>
      </el-form>
      <div v-if="shareDialog.result" class="share-result">
        <div class="share-result-icon">
          <el-icon :size="32" color="#fff"><CircleCheck /></el-icon>
        </div>
        <div class="share-result-title">分享创建成功</div>
        <div class="share-result-desc">将以下链接分享给他人即可访问文件</div>
        <div class="share-result-link">
          <code>{{ shareDialog.fullUrl }}</code>
        </div>
        <div v-if="shareDialog.result.password" class="share-result-pwd">
          <span class="pwd-label">访问密码</span>
          <span class="pwd-value">{{ shareDialog.result.password }}</span>
        </div>
        <el-button type="primary" size="large" style="width:100%; margin-top:16px; border-radius:8px" @click="copyShareUrl">
          <el-icon style="margin-right:6px"><CopyDocument /></el-icon>复制分享信息
        </el-button>
      </div>
      <template #footer>
        <el-button @click="shareDialog.visible = false">关闭</el-button>
        <el-button v-if="!shareDialog.result" type="primary" :loading="shareDialog.loading" @click="executeShare">生成分享</el-button>
      </template>
    </el-dialog>

    <!-- ====== 预览对话框 ====== -->
    <el-dialog
      v-model="previewVisible"
      :title="previewFile?.name || '预览'"
      width="80%"
      destroy-on-close
      top="5vh"
    >
      <div class="preview-container">
        <img v-if="!previewError && previewType === 'image'" :src="previewUrl" class="preview-image" @error="previewError = true" />
        <video v-else-if="!previewError && previewType === 'video'" :src="previewUrl" controls autoplay class="preview-video" @error="previewError = true" />
        <audio v-else-if="!previewError && previewType === 'audio'" :src="previewUrl" controls autoplay class="preview-audio" @error="previewError = true" />
        <iframe v-else-if="!previewError && previewType === 'pdf'" :src="previewUrl" class="preview-pdf" @error="previewError = true" />
        <pre v-else-if="!previewError && previewType === 'text'" class="preview-text">{{ previewTextContent }}</pre>
        <div v-if="previewError" class="preview-unsupported preview-error">
          <el-icon :size="48" color="#F56C6C"><Document /></el-icon>
          <p>预览加载失败</p>
          <el-button type="primary" size="small" @click="downloadFile(previewFile)" style="margin-top:12px">
            <el-icon style="margin-right:4px"><Download /></el-icon>下载文件
          </el-button>
        </div>
        <div v-else-if="!previewType" class="preview-unsupported">
          <el-icon :size="48" color="#909399"><Document /></el-icon>
          <p>此文件类型不支持预览</p>
          <el-button type="primary" size="small" @click="downloadFile(previewFile)" style="margin-top:12px">
            <el-icon style="margin-right:4px"><Download /></el-icon>下载文件
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>
<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fileApi, storageApi, shareApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { ElTable } from 'element-plus'
import FileIcon from '@/components/FileIcon.vue'
import { useUserStore } from '@/store/user'
import { useSiteStore } from "@/store/site"
import { Base64 } from 'js-base64'

const userStore = useUserStore()
const siteStore = useSiteStore()
const perm = (key: string) => userStore.hasPermission(key)

async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    // Fallback for non-HTTPS: use textarea + execCommand
    const ta = document.createElement('textarea')
    ta.value = text
    ta.style.cssText = 'position:fixed;left:-9999px;top:-9999px'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
  }
}

const route = useRoute()
const router = useRouter()
const storageId = computed(() => Number(route.params.id))
const currentPath = ref('/')
const files = ref<any[]>([])
const loading = ref(false)
const viewMode = ref<'table' | 'grid'>('table')
const searchKeyword = ref('')
const isSearching = ref(false)
const storageInfo = ref<any>(null)
const tableRef = ref<InstanceType<typeof ElTable>>()
const uploadFileInput = ref<HTMLInputElement>()
const uploadFolderInput = ref<HTMLInputElement>()

// 目录大小缓存
const dirSizeCache = ref<Record<string, number | null>>({})
const dirSizeLoading = ref<Record<string, boolean>>({})

async function loadDirSize(dirPath: string) {
  if (dirSizeCache.value[dirPath] !== undefined || dirSizeLoading.value[dirPath]) return
  dirSizeLoading.value[dirPath] = true
  try {
    const res: any = await fileApi.dirSize(storageId.value, dirPath)
    dirSizeCache.value[dirPath] = res.size || 0
  } catch {
    dirSizeCache.value[dirPath] = null
  } finally {
    dirSizeLoading.value[dirPath] = false
  }
}

// ---- 多选 ----
const selectedFiles = ref<any[]>([])

function onSelectionChange(rows: any[]) { selectedFiles.value = rows }
function clearSelection() {
  tableRef.value?.clearSelection()
  files.value.forEach(f => f._checked = false)
  selectedFiles.value = []
}
function isFileSelected(file: any) { return selectedFiles.value.some(f => f.path === file.path) }
function onGridClick(file: any) {
  const idx = selectedFiles.value.findIndex(f => f.path === file.path)
  if (idx >= 0) { selectedFiles.value.splice(idx, 1); file._checked = false }
  else { selectedFiles.value.push(file); file._checked = true }
}
function toggleGridSelect(file: any) { onGridClick(file) }
function onGridCheckChange(file: any, checked: boolean) {
  if (checked) { if (!selectedFiles.value.some(f => f.path === file.path)) selectedFiles.value.push(file) }
  else { const idx = selectedFiles.value.findIndex(f => f.path === file.path); if (idx >= 0) selectedFiles.value.splice(idx, 1) }
}

// ---- 拖拽上传 ----
const isDragging = ref(false)
let dragCounter = 0

function onDragOver(e: DragEvent) { e.preventDefault(); dragCounter++; isDragging.value = true }
function onDragLeave() { dragCounter--; if (dragCounter <= 0) { isDragging.value = false; dragCounter = 0 } }

async function onDrop(e: DragEvent) {
  isDragging.value = false; dragCounter = 0
  const dt = e.dataTransfer
  if (!dt) return

  const allFiles: File[] = []
  const emptyDirs: string[] = []

  // 方法1: 用 DataTransferItemList (支持文件夹递归)
  if (dt.items?.length) {
    const collectEntries = async (entry: any, prefix = ''): Promise<void> => {
      if (!entry) return
      if (entry.isFile) {
        try {
          const file = await new Promise<File>((resolve, reject) => {
            entry.file(resolve, reject)
          })
          const relPath = prefix ? prefix + entry.name : entry.name
          Object.defineProperty(file, 'webkitRelativePath', { value: relPath, writable: false })
          allFiles.push(file)
        } catch {}
      } else if (entry.isDirectory) {
        const dirPrefix = prefix ? prefix + entry.name + '/' : entry.name + '/'
        const reader = entry.createReader()
        // readEntries 可能分批返回，需要循环读取
        let entries: any[] = []
        await new Promise<void>((resolve) => {
          const readBatch = () => {
            reader.readEntries((batch: any[]) => {
              if (batch.length === 0) {
                resolve()
              } else {
                entries = entries.concat(batch)
                readBatch()
              }
            }, () => resolve())
          }
          readBatch()
        })
        // 记录空目录
        if (entries.length === 0) {
          const dirPath = prefix ? prefix + entry.name : entry.name
          emptyDirs.push(dirPath)
        }
        for (const child of entries) {
          await collectEntries(child, dirPrefix)
        }
      }
    }
    const items: any[] = []
    for (let i = 0; i < dt.items.length; i++) {
      const item = dt.items[i]
      if (item.kind === 'file') {
        const entry = item.webkitGetAsEntry?.() || item.getAsEntry?.()
        if (entry) items.push(entry)
      }
    }
    for (const entry of items) {
      await collectEntries(entry)
    }
  }

  // 方法2: fallback — 直接用 files
  if (!allFiles.length && dt.files?.length) {
    for (let i = 0; i < dt.files.length; i++) allFiles.push(dt.files[i])
  }

  if (allFiles.length || emptyDirs.length) {
    console.log(`[upload] collected ${allFiles.length} files, ${emptyDirs.length} empty dirs`)
    await uploadFilesWithProgress(allFiles, emptyDirs)
  }
}

// ---- 上传进度 (带速度) ----
const uploadState = reactive({
  uploading: false,
  total: 0,
  done: 0,
  totalPercent: 0,
  currentName: '',
  filePercent: 0,
  speed: '',
})

async function uploadFilesWithProgress(fileList: File[], emptyDirs: string[] = []) {
  uploadState.uploading = true
  uploadState.total = fileList.length
  uploadState.done = 0
  uploadState.totalPercent = fileList.length ? 0 : 100
  uploadState.filePercent = 0
  uploadState.speed = ''

  // 收集需要创建的目录
  const dirsToCreate = new Set<string>()
  for (const file of fileList) {
    const relPath = (file as any).webkitRelativePath as string | undefined
    if (relPath) {
      const dirPart = relPath.includes('/') ? relPath.substring(0, relPath.lastIndexOf('/')) : ''
      if (dirPart) {
        const targetDir = currentPath.value === '/' ? `/${dirPart}` : `${currentPath.value}/${dirPart}`
        dirsToCreate.add(targetDir)
      }
    }
  }
  // 自动创建目录（按深度排序，先建父目录）
  const sortedDirs = [...dirsToCreate].sort((a, b) => a.split('/').length - b.split('/').length)
  for (const dir of sortedDirs) {
    try { await fileApi.mkdir(storageId.value, dir) } catch {}
  }

  // 创建拖拽收集到的空目录
  for (const dirPath of emptyDirs) {
    const targetDir = currentPath.value === '/' ? `/${dirPath}` : `${currentPath.value}/${dirPath}`
    try { await fileApi.mkdir(storageId.value, targetDir) } catch {}
  }

  let success = 0
  for (const file of fileList) {
    // 计算实际上传路径
    const relPath = (file as any).webkitRelativePath as string | undefined
    let uploadPath = currentPath.value
    if (relPath && relPath.includes('/')) {
      const dirPart = relPath.substring(0, relPath.lastIndexOf('/'))
      uploadPath = currentPath.value === '/' ? `/${dirPart}` : `${currentPath.value}/${dirPart}`
    }

    uploadState.currentName = relPath || file.name
    uploadState.filePercent = 0
    uploadState.speed = '计算中...'

    const startTime = Date.now()
    let lastLoaded = 0
    let lastTime = startTime

    try {
      // 上传文件夹时，创建一个新的 File 对象，filename 只保留文件名（去掉路径前缀）
      let uploadFile: File = file
      if (relPath && relPath.includes('/')) {
        const pureName = relPath.substring(relPath.lastIndexOf('/') + 1)
        uploadFile = new File([file], pureName, { type: file.type, lastModified: file.lastModified })
      }

      // 尝试获取直传 URL
      let usedDirect = false
      try {
        const urlRes: any = await fileApi.getUploadUrl(storageId.value, uploadPath, uploadFile.name)
        if (urlRes.supports_direct) {
          // 直传到云存储
          await new Promise<void>((resolve, reject) => {
            const xhr = new XMLHttpRequest()
            xhr.open(urlRes.method || 'PUT', urlRes.url)
            // 设置自定义 headers
            if (urlRes.headers) {
              for (const [k, v] of Object.entries(urlRes.headers)) {
                xhr.setRequestHeader(k, v as string)
              }
            }
            xhr.setRequestHeader('Content-Type', 'application/octet-stream')
            xhr.upload.onprogress = (e) => {
              if (e.lengthComputable) {
                uploadState.filePercent = Math.round((e.loaded / e.total) * 100)
                const now = Date.now()
                const timeDiff = (now - lastTime) / 1000
                if (timeDiff > 0.3) {
                  const bytesDiff = e.loaded - lastLoaded
                  uploadState.speed = formatSpeed(bytesDiff / timeDiff)
                  lastLoaded = e.loaded
                  lastTime = now
                }
              }
            }
            xhr.onload = () => {
              if (xhr.status >= 200 && xhr.status < 300) resolve()
              else reject(new Error(`HTTP ${xhr.status}`))
            }
            xhr.onerror = () => reject(new Error('网络错误'))
            xhr.send(uploadFile)
          })
          // 回调记录日志
          const remotePath = uploadPath === '/' ? `/${uploadFile.name}` : `${uploadPath}/${uploadFile.name}`
          await fileApi.uploadCallback(storageId.value, remotePath, uploadFile.name, uploadFile.size)
          usedDirect = true
          success++
        }
      } catch (e) {
        console.warn('[upload] direct upload failed, falling back to proxy', e)
      }

      // 回退：通过后端代理上传
      if (!usedDirect) {
        const res: any = await fileApi.upload(storageId.value, uploadPath, uploadFile, (progressEvent: any) => {
          const loaded = progressEvent.loaded
          const total = progressEvent.total || file.size
          uploadState.filePercent = total > 0 ? Math.round((loaded / total) * 100) : 0

          // 计算瞬时速度 (每300ms更新一次)
          const now = Date.now()
          const timeDiff = (now - lastTime) / 1000
          if (timeDiff > 0.3) {
            const bytesDiff = loaded - lastLoaded
            const speedBps = bytesDiff / timeDiff
            uploadState.speed = formatSpeed(speedBps)
            lastLoaded = loaded
            lastTime = now
          }
        })
        if (res.success) success++
      }
    } catch {}

    uploadState.done++
    uploadState.totalPercent = Math.round((uploadState.done / uploadState.total) * 100)
  }

  uploadState.uploading = false
  uploadState.currentName = ''
  uploadState.speed = ''
  const dirMsg = emptyDirs.length ? `，${emptyDirs.length} 个空目录` : ''
  if (fileList.length) {
    ElMessage.success(`上传完成: ${success}/${fileList.length}${dirMsg}`)
  } else if (emptyDirs.length) {
    ElMessage.success(`已创建 ${emptyDirs.length} 个空目录`)
  }
  await loadFiles(currentPath.value)
}

function formatSpeed(bytesPerSec: number): string {
  if (bytesPerSec < 1024) return bytesPerSec.toFixed(0) + ' B/s'
  if (bytesPerSec < 1024 * 1024) return (bytesPerSec / 1024).toFixed(1) + ' KB/s'
  return (bytesPerSec / (1024 * 1024)).toFixed(2) + ' MB/s'
}

function triggerUploadFile() { closeContextMenu(); uploadFileInput.value?.click() }
function triggerUploadFolder() { closeContextMenu(); uploadFolderInput.value?.click() }
function handleUploadCommand(cmd: string) {
  if (cmd === 'file') triggerUploadFile()
  else if (cmd === 'folder') triggerUploadFolder()
}
async function onUploadFiles(e: Event) {
  const input = e.target as HTMLInputElement
  if (!input.files?.length) return
  await uploadFilesWithProgress(Array.from(input.files))
  input.value = ''
}

// ---- 批量删除 ----
async function batchDelete() {
  if (!selectedFiles.value.length) return
  try { await ElMessageBox.confirm(`确定删除选中的 ${selectedFiles.value.length} 项？`, '批量删除', { type: 'warning' }) } catch { return }
  loading.value = true; let success = 0, fail = 0
  for (const file of [...selectedFiles.value]) {
    try {
      const fn = file.is_dir ? fileApi.deleteFolder : fileApi.deleteFile
      const res: any = await fn(storageId.value, file.path)
      if (res.success) success++; else { fail++; if (res.message) ElMessage.warning(`${file.name}: ${res.message}`) }
    } catch { fail++ }
  }
  loading.value = false; clearSelection()
  ElMessage.success(`删除完成: ${success} 成功${fail > 0 ? `，${fail} 失败` : ''}`)
  await loadFiles(currentPath.value)
}

// ---- Context Menu ----
const contextMenu = reactive({ visible: false, x: 0, y: 0, target: null as any })
function onRowContextMenu(row: any, colOrEvent?: any, e?: MouseEvent) {
  const event = e || colOrEvent
  if (event?.preventDefault) event.preventDefault()
  if (event?.stopPropagation) event.stopPropagation()
  contextMenu.target = row
  showContextMenu(event)
}
function onBlankContextMenu(e: MouseEvent) {
  const t = e.target as HTMLElement
  if (t.closest('.el-table') || t.closest('.file-grid')) { e.preventDefault(); contextMenu.target = null; showContextMenu(e) }
}
function showContextMenu(e: MouseEvent) {
  let x = e.clientX, y = e.clientY
  if (x + 200 > window.innerWidth) x = window.innerWidth - 208
  if (y + 300 > window.innerHeight) y = window.innerHeight - 308
  contextMenu.x = x; contextMenu.y = y; contextMenu.visible = true
}
function closeContextMenu() { contextMenu.visible = false }

// ---- Breadcrumb ----
const breadcrumbs = computed(() => {
  const parts = currentPath.value.split('/').filter(Boolean)
  return parts.map((name, idx) => ({ name, path: '/' + parts.slice(0, idx + 1).join('/') }))
})

// ---- Core ----
async function loadFiles(path = '/') {
  loading.value = true
  dirSizeCache.value = {} // 清空目录大小缓存
  try {
    const res: any = await fileApi.list(storageId.value, path)
    files.value = (res.files || []).map((f: any) => ({ ...f, _checked: false }))
    currentPath.value = path; isSearching.value = false; selectedFiles.value = []
  } catch { files.value = [] } finally { loading.value = false }
}
function goTo(path: string) { router.push({ query: { path } }) }
function refresh() { closeContextMenu(); loadFiles(currentPath.value) }
function openFile(file: any) {
  closeContextMenu()
  if (file.is_dir) {
    router.push({ query: { path: file.path } })
    return
  }
  // 判断是否可预览
  const ext = file.name.includes('.') ? file.name.split('.').pop()?.toLowerCase() : ''
  if (imageExts.includes(ext)) previewType.value = 'image'
  else if (videoExts.includes(ext)) previewType.value = 'video'
  else if (audioExts.includes(ext)) previewType.value = 'audio'
  else if (pdfExts.includes(ext)) previewType.value = 'pdf'
  else if (textExts.includes(ext)) previewType.value = 'text'
  else previewType.value = ''
  previewFile.value = file
  previewError.value = false
  previewTextContent.value = ''
  const ps = siteStore.get('preview_server')
  if (ps) {
    fileApi.previewUrl(storageId.value, file.path).then((res: any) => {
      const fileUrl = res.url
      const encoded = Base64.encode(fileUrl)
      window.open(ps.replace(/\/+$/, '') + '/onlinePreview?url=' + encodeURIComponent(encoded))
    }).catch(() => {
      ElMessage.error('获取预览链接失败')
    })
  } else {
    const relativeUrl = `/api/files/${storageId.value}/preview?path=${encodeURIComponent(file.path)}`
    previewUrl.value = relativeUrl
    previewVisible.value = true
    if (previewType.value === 'text') {
      fetch(relativeUrl).then(r => {
        if (!r.ok) throw new Error('加载失败')
        return r.text()
      }).then(t => {
        previewTextContent.value = t
      }).catch(() => {
        previewError.value = true
      })
    }
  }
}
function handleDblClick(file: any) { openFile(file) }
function openInNewTab(file: any) {
  closeContextMenu()
  if (file.is_dir) { const rd = router.resolve({ path: `/files/${storageId.value}`, query: { path: file.path } }); window.open(rd.href, '_blank') }
  else downloadFile(file)
}
async function downloadFile(file: any) {
  closeContextMenu()
  try {
    const res: any = await fileApi.getDownloadUrl(storageId.value, file.path)
    const url = res.url || `/api/files/${storageId.value}/serve?path=${encodeURIComponent(file.path)}`
    // fetch + blob 保留原文件名
    const resp = await fetch(url)
    const blob = await resp.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = file.name
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(a.href)
  } catch { ElMessage.error('下载失败') }
}
async function copyDirectLink(file: any) {
  closeContextMenu()
  let url: string
  try {
    const res: any = await fileApi.directLink(storageId.value, file.path)
    url = res.url || `/api/files/${storageId.value}/serve?path=${encodeURIComponent(file.path)}`
    if (url.startsWith('/')) url = window.location.origin + url
  } catch { ElMessage.error('获取链接失败'); return }
  await copyToClipboard(url)
  ElMessage.success('直链已复制')
}
async function copyDownloadLink(file: any) {
  closeContextMenu()
  const url = `${window.location.origin}/api/files/${storageId.value}/serve?path=${encodeURIComponent(file.path)}`
  await copyToClipboard(url)
  ElMessage.success('下载链接已复制')
}
async function deleteItem(file: any) {
  closeContextMenu()
  try {
    await ElMessageBox.confirm(`确定删除 "${file.name}" ?`, '确认删除', { type: 'warning' })
    const fn = file.is_dir ? fileApi.deleteFolder : fileApi.deleteFile
    const res: any = await fn(storageId.value, file.path)
    if (res.success) { ElMessage.success('已删除'); await loadFiles(currentPath.value) } else ElMessage.error(res.message || '删除失败')
  } catch {}
}
async function renameItem(file: any) {
  closeContextMenu()
  try {
    const { value } = await ElMessageBox.prompt('输入新名称', '重命名', { inputValue: file.name, inputPattern: /^[^\\/]+$/, inputErrorMessage: '名称不能为空' })
    if (value === file.name) return
    const res: any = await fileApi.rename(storageId.value, file.path, value)
    if (res.success) { ElMessage.success('重命名成功'); await loadFiles(currentPath.value) }
  } catch {}
}
async function showMkdir() {
  closeContextMenu()
  try {
    const { value } = await ElMessageBox.prompt('输入文件夹名称', '新建文件夹', { inputPattern: /^[^\\/]+$/, inputErrorMessage: '名称不能为空' })
    const p = currentPath.value === '/' ? `/${value}` : `${currentPath.value}/${value}`
    const res: any = await fileApi.mkdir(storageId.value, p)
    if (res.success) { ElMessage.success('创建成功'); await loadFiles(currentPath.value) }
  } catch {}
}
async function doSearch() {
  if (!searchKeyword.value.trim()) return
  loading.value = true
  try { const res: any = await fileApi.search(storageId.value, searchKeyword.value, currentPath.value); files.value = (res.files || []).map((f: any) => ({ ...f, _checked: false })); isSearching.value = true }
  catch { files.value = [] } finally { loading.value = false }
}
function clearSearch() { searchKeyword.value = ''; isSearching.value = false; loadFiles(currentPath.value) }

// ---- Move / Copy ----
const moveDialog = reactive({ visible: false, title: '', action: 'move' as 'move' | 'copy', files: [] as any[], targetPath: '/', dirTree: [] as { path: string; label: string }[], newFolderName: '', loading: false })
async function showMoveDialog(file: any) { closeContextMenu(); moveDialog.action = 'move'; moveDialog.title = '移动到...'; moveDialog.files = [file]; moveDialog.targetPath = '/'; moveDialog.newFolderName = ''; await loadDirTree(); moveDialog.visible = true }
async function showCopyDialog(file: any) { closeContextMenu(); moveDialog.action = 'copy'; moveDialog.title = '复制到...'; moveDialog.files = [file]; moveDialog.targetPath = '/'; moveDialog.newFolderName = ''; await loadDirTree(); moveDialog.visible = true }
function batchMove() {
  if (!selectedFiles.value.length) return
  moveDialog.action = 'move'; moveDialog.title = `批量移动 ${selectedFiles.value.length} 项到...`; moveDialog.files = [...selectedFiles.value]; moveDialog.targetPath = '/'; moveDialog.newFolderName = ''; loadDirTree(); moveDialog.visible = true
}
async function loadDirTree() {
  // 根节点
  const root: any = { path: '/', name: '根目录', children: [], leaf: false }
  // 加载根目录的子目录
  try {
    const res: any = await fileApi.list(storageId.value, '/')
    root.children = (res.files || []).filter((f: any) => f.is_dir).map((f: any) => ({
      path: f.path, name: f.name, children: [], leaf: false,
    }))
  } catch {}
  moveDialog.dirTree = [root]
  moveDialog.targetPath = '/'
}

async function loadTreeChildren(node: any, resolve: Function) {
  if (node.level === 0) { resolve(moveDialog.dirTree); return }
  try {
    const res: any = await fileApi.list(storageId.value, node.data.path)
    const dirs = (res.files || []).filter((f: any) => f.is_dir).map((f: any) => ({
      path: f.path, name: f.name, children: [], leaf: false,
    }))
    resolve(dirs)
  } catch { resolve([]) }
}
async function createAndSelectFolder() {
  if (!moveDialog.newFolderName.trim()) return
  const parent = moveDialog.targetPath === '/' ? '' : moveDialog.targetPath
  const newPath = `${parent}/${moveDialog.newFolderName.trim()}`
  try { const res: any = await fileApi.mkdir(storageId.value, newPath); if (res.success) { moveDialog.targetPath = newPath; moveDialog.newFolderName = ''; await loadDirTree(); ElMessage.success('文件夹已创建') } } catch {}
}
async function executeMoveCopy() {
  if (!moveDialog.files.length) return
  const destDir = moveDialog.targetPath === '/' ? '' : moveDialog.targetPath
  moveDialog.loading = true
  const fn = moveDialog.action === 'move' ? fileApi.move : fileApi.copy
  let success = 0, fail = 0
  for (const file of moveDialog.files) {
    const destPath = `${destDir}/${file.name}`
    if (file.path === destPath) { fail++; continue }
    try {
      const res: any = await fn(storageId.value, file.path, destPath)
      if (res.success) success++; else { fail++; if (res.message) ElMessage.warning(`${file.name}: ${res.message}`) }
    } catch { fail++ }
  }
  moveDialog.loading = false; moveDialog.visible = false
  ElMessage.success(`${moveDialog.action === 'move' ? '移动' : '复制'}完成: ${success} 成功${fail > 0 ? `，${fail} 失败` : ''}`)
  clearSelection(); await loadFiles(currentPath.value)
}

// ---- Share ----
const shareDialog = reactive({ visible: false, files: [] as any[], password: '', passwordEnabled: false, allowDownload: true, expireHours: -1, maxViews: 0, loading: false, result: null as any, fullUrl: '' })

// 预览
const previewVisible = ref(false)
const previewFile = ref<any>(null)
const previewUrl = ref('')
const previewType = ref('')
const previewError = ref(false)
const previewTextContent = ref('')
const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp', 'bmp', 'ico', 'avif']
const videoExts = ['mp4', 'webm', 'ogg', 'mov', 'mkv', 'avi']
const audioExts = ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a']
const pdfExts = ['pdf']
const textExts = ['txt', 'md', 'json', 'xml', 'csv', 'log', 'ini', 'yaml', 'yml', 'toml', 'cfg', 'conf', 'env',
  'html', 'css', 'js', 'ts', 'jsx', 'tsx', 'vue', 'svelte', 'styl',
  'py', 'java', 'go', 'rs', 'c', 'cpp', 'h', 'hpp', 'cs', 'rb', 'php', 'swift', 'kt', 'scala', 'lua', 'r', 'm',
  'pl', 'pm', 'clj', 'erl', 'jl', 'pas', 'scm', 'tcl', 'coffee', 'bf',
  'vb', 'vbs',
  'sh', 'bash', 'zsh', 'bat', 'ps1', 'cmd',
  'sql', 'graphql', 'proto',
  'dockerfile', 'makefile', 'gitignore', 'editorconfig']

function showShareDialog(file: any) { closeContextMenu(); shareDialog.files = [file]; shareDialog.password = ''; shareDialog.passwordEnabled = false; shareDialog.allowDownload = true; shareDialog.expireHours = -1; shareDialog.maxViews = 0; shareDialog.result = null; shareDialog.fullUrl = ''; shareDialog.visible = true }
function batchShare() {
  if (!selectedFiles.value.length) return
  shareDialog.files = [...selectedFiles.value]; shareDialog.password = ''; shareDialog.passwordEnabled = false; shareDialog.allowDownload = true; shareDialog.expireHours = -1; shareDialog.maxViews = 0; shareDialog.result = null; shareDialog.fullUrl = ''; shareDialog.visible = true
}
function generatePassword(): string {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789'
  let result = ''
  for (let i = 0; i < 6; i++) result += chars[Math.floor(Math.random() * chars.length)]
  return result
}

async function executeShare() {
  if (!shareDialog.files.length) return; shareDialog.loading = true
  try {
    const isMulti = shareDialog.files.length > 1
    const payload: any = {
      storage_id: storageId.value,
      file_path: isMulti ? JSON.stringify(shareDialog.files.map(f => f.path)) : shareDialog.files[0].path,
      is_dir: isMulti ? false : shareDialog.files[0].is_dir,
      is_multi: isMulti,
      file_name: isMulti ? shareDialog.files.map(f => f.name).join('、') : shareDialog.files[0].name,
      allow_download: shareDialog.allowDownload,
      password: shareDialog.password || null,
      expire_hours: shareDialog.expireHours || null,
      max_views: shareDialog.maxViews || null,
    }
    const res: any = await shareApi.create(payload)
    shareDialog.result = res; shareDialog.fullUrl = `${window.location.origin}${res.share_url}`
  } catch {} finally { shareDialog.loading = false }
}
function copyShareUrl() {
  let text = `链接：${shareDialog.fullUrl}`
  if (shareDialog.result?.password) text += `\n密码：${shareDialog.result.password}`
  navigator.clipboard.writeText(text).then(() => ElMessage.success('已复制到剪贴板')).catch(() => {
    const ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); ElMessage.success('已复制到剪贴板')
  })
}

// ---- Util ----
function formatSize(bytes: number | null | undefined): string {
  if (!bytes) return '0 B'; const u = ['B', 'KB', 'MB', 'GB', 'TB']; const i = Math.floor(Math.log(bytes) / Math.log(1024)); return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + u[i]
}
function onKeyDown(e: KeyboardEvent) { if (e.key === 'Delete' && selectedFiles.value.length) batchDelete(); else if (e.key === 'F5') { e.preventDefault(); refresh() } }

// ---- Lifecycle ----
watch(() => route.query.path, (p) => loadFiles((p as string) || '/'), { immediate: true })
onMounted(async () => { try { storageInfo.value = await storageApi.get(storageId.value) } catch {}; document.addEventListener('keydown', onKeyDown) })
onBeforeUnmount(() => { document.removeEventListener('keydown', onKeyDown) })
</script>

<style scoped>
.file-page { position: relative; min-height: calc(100vh - 200px); }
.file-page--dragging { outline: 2px dashed #409EFF; outline-offset: -2px; }
.drag-overlay {
  position: fixed; inset: 0; z-index: 9000;
  background: rgba(64, 158, 255, 0.08);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  pointer-events: none;
}
.batch-bar {
  margin-top: 10px; padding: 8px 12px;
  background: #fdf6ec; border-radius: 4px;
  display: flex; align-items: center; gap: 12px; font-size: 13px;
}
.upload-progress-bar { margin-top: 10px; padding: 8px 12px; background: #f0f9ff; border-radius: 4px; }
.file-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px; padding: 8px; min-height: 200px;
}
.file-grid-item {
  display: flex; flex-direction: column; align-items: center;
  padding: 16px 8px; border-radius: 8px; cursor: pointer;
  transition: background 0.2s; border: 2px solid transparent; position: relative;
}
.file-grid-item:hover { background: #f0f9ff; }
.file-grid-item--selected { background: #ecf5ff; border-color: #409EFF; }
.file-grid-check { position: absolute; top: 4px; left: 4px; }
.file-grid-name {
  margin-top: 8px; font-size: 13px; text-align: center;
  word-break: break-all; max-width: 120px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.file-grid-actions {
  display: flex; align-items: center; gap: 0; margin-top: 6px;
  opacity: 0; transition: opacity 0.2s;
}
.file-grid-item:hover .file-grid-actions { opacity: 1; }
.context-menu {
  position: fixed; z-index: 9999; background: #fff;
  border-radius: 8px; box-shadow: 0 6px 24px rgba(0,0,0,0.15);
  padding: 6px 0; min-width: 180px; user-select: none;
}
.ctx-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 16px; font-size: 13px; color: #303133;
  cursor: pointer; transition: background 0.15s;
}
.ctx-item:hover { background: #f0f9ff; color: #409EFF; }
.ctx-item--danger:hover { background: #fef0f0; color: #F56C6C; }
.ctx-item .el-icon { font-size: 15px; }
.ctx-divider { height: 1px; background: #ebeef5; margin: 4px 0; }
.dir-tree-box {
  max-height: 320px; overflow-y: auto;
  border: 1px solid #dcdfe6; border-radius: 6px; padding: 8px;
}

/* 移动/复制弹窗 */
.move-file-info {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 16px; padding: 10px 14px;
  background: #f5f7fa; border-radius: 8px;
}
.move-file-icon {
  width: 36px; height: 36px; border-radius: 8px;
  background: linear-gradient(135deg, #409EFF, #66b1ff);
  display: flex; align-items: center; justify-content: center;
}
.move-file-name {
  font-size: 14px; font-weight: 600; color: #303133;
}
.move-section-label {
  font-size: 12px; color: #909399; margin-bottom: 6px; font-weight: 600;
}
.move-target-display {
  display: flex; align-items: center; gap: 6px;
  margin-top: 10px; padding: 8px 12px;
  background: #ecf5ff; border-radius: 6px;
  font-size: 12px; color: #409EFF;
}

/* 分享结果 */
/* Preview dialog */
.preview-container {
  min-height: 360px;
  max-height: 80vh;
  background: #111827;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preview-image {
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
}
.preview-video {
  width: 100%;
  max-height: 80vh;
  background: #000;
}
.preview-audio {
  width: min(640px, 90%);
}
.preview-pdf {
  width: 100%;
  height: 80vh;
  border: 0;
  background: #fff;
}
.preview-text {
  width: 100%;
  max-height: 80vh;
  margin: 0;
  padding: 16px 20px;
  overflow: auto;
  background: #fff;
  color: #1d2129;
  font-family: 'Menlo', 'Monaco', 'Consolas', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
  text-align: left;
}
.preview-unsupported {
  width: 100%;
  min-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #d1d5db;
  background: #f5f7fa;
}
.preview-unsupported p {
  margin: 12px 0 0;
  color: #606266;
}
.preview-error {
  background: #fef0f0;
}

.share-result {
  margin-top: 16px; padding: 24px; text-align: center;
  background: linear-gradient(135deg, #667eea11, #764ba211);
  border-radius: 12px; border: 1px solid #e8e8ec;
}
.share-result-icon {
  width: 56px; height: 56px; border-radius: 50%; margin: 0 auto 12px;
  background: linear-gradient(135deg, #67c23a, #85ce61);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 6px 16px rgba(103, 194, 58, 0.3);
}
.share-result-title {
  font-size: 18px; font-weight: 700; color: #303133; margin-bottom: 4px;
}
.share-result-desc {
  font-size: 13px; color: #909399; margin-bottom: 16px;
}
.share-result-link {
  background: #f5f7fa; border-radius: 8px; padding: 10px 16px; margin-bottom: 12px;
}
.share-result-link code {
  font-size: 13px; color: #409EFF; word-break: break-all; font-family: monospace;
}
.share-result-pwd {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  margin-bottom: 4px;
}
.pwd-label {
  font-size: 12px; color: #909399; background: #f5f7fa;
  padding: 2px 8px; border-radius: 4px;
}
.pwd-value {
  font-size: 16px; font-weight: 700; color: #e6a23c; font-family: monospace;
  letter-spacing: 2px;
}
</style>

<template>
  <div class="settings-page">
    <el-card class="settings-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <h2>站点设置</h2>
            <span class="header-desc">管理站点基本信息、品牌标识和备案</span>
          </div>
          <el-button type="primary" :loading="saving" @click="saveSettings" round>
            <el-icon style="margin-right: 6px"><Check /></el-icon>保存设置
          </el-button>
        </div>
      </template>

      <el-tabs v-model="activeTab" class="settings-tabs">
        <!-- 基本信息 -->
        <el-tab-pane label="基本信息" name="basic">
          <div class="tab-content">
            <el-form label-width="100px" class="settings-form">
              <el-form-item label="站点名称">
                <el-input v-model="form.site_name" placeholder="请输入站点名称" maxlength="50" show-word-limit />
              </el-form-item>
              <el-form-item label="站点描述">
                <el-input v-model="form.site_description" placeholder="请输入站点描述" type="textarea" :rows="3" maxlength="200" show-word-limit />
              </el-form-item>
              <el-form-item label="ICP备案号">
                <el-input v-model="form.icp_number" placeholder="京ICP备XXXXXXXX号" />
                <div class="form-tip">填写后将在页面底部显示备案信息</div>
              </el-form-item>
              <el-form-item label="登录入口">
                <el-switch v-model="loginButtonEnabled" active-text="显示" inactive-text="隐藏" />
                <div class="form-tip">控制首页是否显示登录按钮</div>
              </el-form-item>
              <el-form-item label="图片验证码">
                <el-switch v-model="captchaEnabled" active-text="启用" inactive-text="禁用" />
                <div class="form-tip">登录时是否需要输入图片验证码</div>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- 品牌标识 -->
        <el-tab-pane label="品牌标识" name="brand">
          <div class="tab-content">
            <div class="brand-section">
              <!-- Logo 上传 -->
              <div class="brand-block">
                <div class="brand-label">站点 Logo</div>
                <div class="brand-row">
                  <div
                    class="upload-box"
                    :class="{ 'has-image': form.site_logo }"
                    @click="triggerUpload('logo')"
                  >
                    <template v-if="form.site_logo">
                      <img :src="form.site_logo" class="preview-img" @error="($event.target as HTMLImageElement).style.display='none'" />
                      <div class="upload-mask">
                        <el-icon :size="20"><RefreshRight /></el-icon>
                        <span>更换</span>
                      </div>
                    </template>
                    <template v-else>
                      <el-icon :size="28" color="#c0c4cc"><Plus /></el-icon>
                      <span class="upload-text">上传 Logo</span>
                    </template>
                  </div>
                  <div class="brand-info">
                    <el-input v-model="form.site_logo" placeholder="或输入图片 URL" clearable size="small" />
                    <p class="brand-tip">支持 JPG / PNG / SVG 格式，建议高度 40px，不超过 2MB</p>
                    <div v-if="form.site_logo" class="current-url">
                      <span class="url-label">当前：</span>
                      <span class="url-text">{{ form.site_logo }}</span>
                    </div>
                  </div>
                  <el-upload
                    ref="logoUploadRef"
                    :show-file-list="false"
                    :before-upload="beforeImageUpload"
                    :http-request="(opt: any) => uploadImage(opt, 'site_logo')"
                    accept="image/*"
                    style="display: none"
                  >
                    <button ref="logoTrigger" />
                  </el-upload>
                </div>
              </div>

              <!-- Favicon 上传 -->
              <div class="brand-block">
                <div class="brand-label">站点图标 (Favicon)</div>
                <div class="brand-row">
                  <div
                    class="upload-box small"
                    :class="{ 'has-image': form.site_favicon }"
                    @click="triggerUpload('favicon')"
                  >
                    <template v-if="form.site_favicon">
                      <img :src="form.site_favicon" class="preview-img favicon" @error="($event.target as HTMLImageElement).style.display='none'" />
                      <div class="upload-mask">
                        <el-icon :size="16"><RefreshRight /></el-icon>
                      </div>
                    </template>
                    <template v-else>
                      <el-icon :size="22" color="#c0c4cc"><Plus /></el-icon>
                      <span class="upload-text">上传图标</span>
                    </template>
                  </div>
                  <div class="brand-info">
                    <el-input v-model="form.site_favicon" placeholder="或输入图标 URL" clearable size="small" />
                    <p class="brand-tip">建议 32×32 或 16×16 的 .ico / .png 图片</p>
                    <div v-if="form.site_favicon" class="current-url">
                      <span class="url-label">当前：</span>
                      <span class="url-text">{{ form.site_favicon }}</span>
                    </div>
                  </div>
                  <el-upload
                    ref="faviconUploadRef"
                    :show-file-list="false"
                    :before-upload="beforeImageUpload"
                    :http-request="(opt: any) => uploadImage(opt, 'site_favicon')"
                    accept="image/*"
                    style="display: none"
                  >
                    <button ref="faviconTrigger" />
                  </el-upload>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 文件预览 -->
        <el-tab-pane label="文件预览" name="preview">
          <div class="tab-content">
            <el-form label-width="140px" class="settings-form">
              <el-form-item label="预览服务器地址">
                <el-input v-model="form.preview_server" placeholder="例如：http://127.0.0.1:8012" clearable />
                <div class="form-tip">使用kkView官网参考：<a href="https://kkview.cn/" target="_blank" rel="noopener">https://kkview.cn/</a>。留空则使用内置预览。</div>
              </el-form-item>
              <el-form-item label="后端 API 地址">
                <el-input v-model="form.backend_url" placeholder="例如：http://127.0.0.1:8000" clearable />
                <div class="form-tip">kkView 需要通过此地址获取文件。留空则使用当前页面地址</div>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { settingsApi } from '@/api'
import { ElMessage } from 'element-plus'
import api from '@/api/index'

const saving = ref(false)
const activeTab = ref('basic')
const logoTrigger = ref<HTMLButtonElement>()
const faviconTrigger = ref<HTMLButtonElement>()

const form = reactive({
  site_name: 'UniFile',
  site_description: '统一文件管理系统',
  site_logo: '',
  site_favicon: '',
  icp_number: '',
  preview_server: '',
  backend_url: '',
  show_login_button: 'true',
  enable_captcha: 'true',
})

const loginButtonEnabled = computed({
  get: () => form.show_login_button === 'true',
  set: (val: boolean) => { form.show_login_button = val ? 'true' : 'false' }
})

const captchaEnabled = computed({
  get: () => form.enable_captcha === 'true',
  set: (val: boolean) => { form.enable_captcha = val ? 'true' : 'false' }
})

function triggerUpload(type: 'logo' | 'favicon') {
  if (type === 'logo') logoTrigger.value?.click()
  else faviconTrigger.value?.click()
}

function beforeImageUpload(file: File) {
  const allowed = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/x-icon', 'image/svg+xml']
  if (!allowed.includes(file.type) && !file.name.match(/\.(jpg|jpeg|png|gif|webp|ico|svg)$/i)) {
    ElMessage.error('只能上传图片格式文件')
    return false
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 2MB')
    return false
  }
  return true
}

async function uploadImage(option: any, field: 'site_logo' | 'site_favicon') {
  try {
    const formData = new FormData()
    formData.append('file', option.file)
    const res: any = await api.post('/settings/upload-image', formData, {})
    form[field] = res.url
    ElMessage.success('图片上传成功')
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '上传失败')
  }
}

async function loadSettings() {
  try {
    const res: any = await settingsApi.get()
    Object.keys(form).forEach(key => {
      if (res[key] !== undefined) (form as any)[key] = res[key]
    })
  } catch {}
}

async function saveSettings() {
  saving.value = true
  try {
    await settingsApi.update({ ...form })
    ElMessage.success('设置已保存')
    const { useSiteStore } = await import('@/store/site')
    const siteStore = useSiteStore()
    await siteStore.loadSettings()
  } catch {} finally { saving.value = false }
}

onMounted(loadSettings)
</script>

<style scoped>
.settings-page {
  padding: 0;
}

.settings-card {
  border: none;
  border-radius: 10px;
}

.settings-card :deep(.el-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left h2 {
  font-size: 17px;
  font-weight: 700;
  color: #1d2129;
  margin: 0 0 2px;
}

.header-desc {
  font-size: 13px;
  color: #909399;
}

/* Tabs */
.settings-tabs :deep(.el-tabs__header) {
  margin: 0;
  padding: 0 24px;
  background: #fafbfc;
}

.settings-tabs :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.settings-tabs :deep(.el-tabs__item) {
  font-size: 14px;
  height: 44px;
  line-height: 44px;
}

.tab-content {
  padding: 24px 0;
  max-width: 560px;
}

/* Form */
.settings-form :deep(.el-form-item) {
  margin-bottom: 22px;
}

.settings-form :deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
.form-tip a {
  color: #409eff;
  text-decoration: none;
}
.form-tip a:hover {
  text-decoration: underline;
}

/* Brand section */
.brand-section {
  display: flex;
  flex-direction: column;
  gap: 28px;
}

.brand-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.brand-label {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.brand-row {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

/* Upload box */
.upload-box {
  position: relative;
  width: 120px;
  height: 100px;
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;
  flex-shrink: 0;
  background: #fafbfc;
}

.upload-box:hover {
  border-color: #2ea9df;
  background: #f0f9ff;
}

.upload-box.has-image {
  border-style: solid;
  border-color: #e4e7ed;
}

.upload-box.small {
  width: 80px;
  height: 80px;
}

.upload-text {
  font-size: 12px;
  color: #909399;
}

.preview-img {
  max-width: 100px;
  max-height: 50px;
  object-fit: contain;
}

.preview-img.favicon {
  max-width: 40px;
  max-height: 40px;
}

.upload-mask {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  color: #fff;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.2s;
  border-radius: 6px;
}

.upload-box:hover .upload-mask {
  opacity: 1;
}

/* Brand info */
.brand-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.brand-tip {
  font-size: 12px;
  color: #909399;
  margin: 0;
  line-height: 1.5;
}

.current-url {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
}

.url-label {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
}

.url-text {
  font-size: 12px;
  color: #606266;
  font-family: monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 300px;
}
</style>

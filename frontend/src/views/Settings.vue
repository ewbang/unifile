<template>
  <div class="settings-page">
    <el-card>
      <template #header>
        <div style="display:flex; align-items:center; justify-content:space-between">
          <span style="font-weight:600; font-size:16px">站点设置</span>
          <el-button type="primary" :loading="saving" @click="saveSettings">
            <el-icon style="margin-right:4px"><Check /></el-icon>保存设置
          </el-button>
        </div>
      </template>

      <el-form label-width="120px" style="max-width:600px">
        <!-- 基本信息 -->
        <div class="section-title">基本信息</div>
        <el-form-item label="站点名称">
          <el-input v-model="form.site_name" placeholder="UniFile" />
        </el-form-item>
        <el-form-item label="站点描述">
          <el-input v-model="form.site_description" placeholder="统一文件管理系统" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="公网访问地址">
          <el-input v-model="form.public_url" placeholder="https://files.example.com" />
          <div class="form-tip">用于生成分享链接的完整地址，留空则使用当前访问地址</div>
        </el-form-item>

        <!-- 品牌标识 -->
        <div class="section-title">品牌标识</div>
        <el-form-item label="站点Logo">
          <el-input v-model="form.site_logo" placeholder="Logo图片URL或留空使用默认" />
          <div v-if="form.site_logo" class="logo-preview">
            <img :src="form.site_logo" alt="Logo预览" @error="($event.target as HTMLImageElement).style.display='none'" />
          </div>
        </el-form-item>
        <el-form-item label="站点图标">
          <el-input v-model="form.site_favicon" placeholder="Favicon图标URL或留空使用默认" />
          <div class="form-tip">建议 32x32 或 16x16 的 .ico 或 .png 图片</div>
        </el-form-item>

        <!-- 备案信息 -->
        <div class="section-title">备案信息</div>
        <el-form-item label="ICP备案号">
          <el-input v-model="form.icp_number" placeholder="京ICP备XXXXXXXX号" />
        </el-form-item>
        <el-form-item label="页脚文字">
          <el-input v-model="form.footer_text" placeholder="自定义页脚文字" />
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { settingsApi } from '@/api'
import { ElMessage } from 'element-plus'

const saving = ref(false)
const form = reactive({
  site_name: '',
  site_description: '',
  site_logo: '',
  site_favicon: '',
  icp_number: '',
  footer_text: '',
  public_url: '',
})

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
    // 刷新全局站点设置
    const { useSiteStore } = await import('@/store/site')
    const siteStore = useSiteStore()
    await siteStore.loadSettings()
  } catch {} finally { saving.value = false }
}

onMounted(loadSettings)
</script>

<style scoped>
.settings-page { max-width: 800px; margin: 0 auto; }
.section-title {
  font-size: 14px; font-weight: 700; color: #303133;
  margin: 20px 0 12px; padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}
.section-title:first-child { margin-top: 0; }
.form-tip { font-size: 12px; color: #909399; margin-top: 4px; }
.logo-preview {
  margin-top: 8px; padding: 8px; background: #f5f7fa;
  border-radius: 6px; display: inline-block;
}
.logo-preview img { max-height: 40px; max-width: 200px; }
</style>

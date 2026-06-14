<template>
  <div class="login-page">
    <canvas ref="bgCanvas" class="bg-canvas" />
    <div class="login-wrapper">
      <!-- 左侧品牌区 -->
      <div class="brand-side">
        <div class="brand-content">
          <div class="brand-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
              <path d="M13 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-5-5z" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="13 2 8 7 14 7" stroke="#fff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <line x1="8" y1="13" x2="16" y2="13" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>
              <line x1="8" y1="17" x2="16" y2="17" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <h1>UniFile</h1>
          <p class="brand-desc">统一文件管理平台</p>
          <div class="brand-features">
            <div class="feature-item"><span class="dot" />多云存储管理</div>
            <div class="feature-item"><span class="dot" />安全文件分享</div>
            <div class="feature-item"><span class="dot" />权限精细控制</div>
          </div>
        </div>
      </div>
      <!-- 右侧表单区 -->
      <div class="form-side">
        <div class="form-header">
          <h2>欢迎回来</h2>
          <p>请登录您的账号</p>
        </div>
        <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" size="large">
              <template #prefix><el-icon><User /></el-icon></template>
            </el-input>
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="密码" size="large" show-password @keyup.enter="handleLogin">
              <template #prefix><el-icon><Lock /></el-icon></template>
            </el-input>
          </el-form-item>
          <el-form-item v-if="siteStore.get('enable_captcha', 'true') === 'true'" prop="captcha">
            <div class="captcha-row">
              <el-input v-model="form.captcha" placeholder="验证码" size="large" maxlength="4" @keyup.enter="handleLogin">
                <template #prefix><el-icon><Key /></el-icon></template>
              </el-input>
              <canvas ref="captchaCanvas" class="captcha-canvas" width="120" height="40" @click="refreshCaptcha" title="点击刷新" />
            </div>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="large" :loading="loading" class="login-btn" @click="handleLogin">
              <span v-if="!loading">登 录</span>
              <span v-else>验证中...</span>
            </el-button>
          </el-form-item>
        </el-form>
        <div class="form-footer">Powered by UniFile</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'
import { useSiteStore } from '@/store/site'
import { ElMessage } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const siteStore = useSiteStore()
const formRef = ref()
const loading = ref(false)
const captchaCanvas = ref<HTMLCanvasElement>()
const bgCanvas = ref<HTMLCanvasElement>()
const captchaCode = ref('')
let animId = 0

const form = reactive({ username: '', password: '', captcha: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  captcha: [{
    validator: (_r: any, _v: any, cb: any) => {
      if (siteStore.get('enable_captcha', 'true') === 'true' && !_v) cb(new Error('请输入验证码'))
      else cb()
    },
    trigger: 'blur'
  }],
}

// ── 粒子背景 ──
function initBg() {
  const canvas = bgCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  let w = canvas.width = window.innerWidth
  let h = canvas.height = window.innerHeight

  const particles: { x: number; y: number; vx: number; vy: number; r: number }[] = []
  const count = Math.floor((w * h) / 14000)
  for (let i = 0; i < count; i++) {
    particles.push({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      r: Math.random() * 2 + 0.8,
    })
  }

  function draw() {
    if (!ctx) return
    ctx.clearRect(0, 0, w, h)

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)'
    ctx.lineWidth = 1
    const gap = 50
    for (let x = 0; x < w; x += gap) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke() }
    for (let y = 0; y < h; y += gap) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke() }

    for (const p of particles) {
      p.x += p.vx; p.y += p.vy
      if (p.x < 0) p.x = w; if (p.x > w) p.x = 0
      if (p.y < 0) p.y = h; if (p.y > h) p.y = 0
      ctx.beginPath()
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(255, 255, 255, 0.4)'
      ctx.fill()
    }

    ctx.lineWidth = 0.5
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x
        const dy = particles[i].y - particles[j].y
        const d = dx * dx + dy * dy
        if (d < 15000) {
          ctx.strokeStyle = `rgba(255, 255, 255, ${0.18 * (1 - d / 15000)})`
          ctx.beginPath()
          ctx.moveTo(particles[i].x, particles[i].y)
          ctx.lineTo(particles[j].x, particles[j].y)
          ctx.stroke()
        }
      }
    }
    animId = requestAnimationFrame(draw)
  }
  draw()

  window.addEventListener('resize', () => {
    w = canvas.width = window.innerWidth
    h = canvas.height = window.innerHeight
  })
}

// ── 验证码 ──
function generateCaptcha(): string {
  return Math.floor(1000 + Math.random() * 9000).toString()
}

function drawCaptcha() {
  const canvas = captchaCanvas.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  captchaCode.value = generateCaptcha()
  const code = captchaCode.value

  ctx.fillStyle = '#f0f8ff'
  ctx.fillRect(0, 0, 120, 40)

  for (let i = 0; i < 5; i++) {
    ctx.strokeStyle = `rgba(46, 169, 223, ${0.15 + Math.random() * 0.15})`
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(Math.random() * 120, Math.random() * 40)
    ctx.lineTo(Math.random() * 120, Math.random() * 40)
    ctx.stroke()
  }

  for (let i = 0; i < 40; i++) {
    ctx.fillStyle = `rgba(46, 169, 223, ${0.2 + Math.random() * 0.25})`
    ctx.beginPath()
    ctx.arc(Math.random() * 120, Math.random() * 40, 1, 0, Math.PI * 2)
    ctx.fill()
  }

  const colors = ['#1a6fa0', '#2EA9DF', '#e6a23c', '#f56c6c', '#67c23a']
  for (let i = 0; i < 4; i++) {
    ctx.font = `bold ${20 + Math.random() * 4}px 'Courier New', monospace`
    ctx.fillStyle = colors[Math.floor(Math.random() * colors.length)]
    ctx.save()
    ctx.translate(18 + i * 25, 28 + (Math.random() - 0.5) * 8)
    ctx.rotate((Math.random() - 0.5) * 0.5)
    ctx.fillText(code[i], 0, 0)
    ctx.restore()
  }
}

function refreshCaptcha() {
  drawCaptcha()
  form.captcha = ''
}

// ── 登录 ──
async function handleLogin() {
  try { await formRef.value?.validate() } catch { return }
  if (siteStore.get('enable_captcha', 'true') === 'true' && form.captcha !== captchaCode.value) {
    ElMessage.error('验证码错误')
    refreshCaptcha()
    return
  }
  loading.value = true
  try {
    await userStore.login(form.username, form.password)
    await userStore.fetchUserInfo()
    await userStore.fetchPermissions()
    ElMessage.success('登录成功')
    router.push((route.query.redirect as string) || '/admin/dashboard')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '登录失败')
    refreshCaptcha()
  } finally { loading.value = false }
}

onMounted(() => { siteStore.loadSettings(); initBg(); drawCaptcha() })
onUnmounted(() => cancelAnimationFrame(animId))
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a6fa0 0%, #238bbe 30%, #2EA9DF 60%, #5ec4f0 100%);
  position: relative;
  overflow: hidden;
  padding: 20px 0;
}
.bg-canvas {
  position: absolute;
  inset: 0;
  z-index: 0;
}

/* ── 登录容器：左右布局 ── */
.login-wrapper {
  display: flex;
  width: 820px;
  min-height: 460px;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  position: relative;
  z-index: 1;
}

/* ── 左侧品牌区 ── */
.brand-side {
  width: 320px;
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 32px;
}
.brand-content {
  text-align: center;
}
.brand-icon {
  width: 72px;
  height: 72px;
  margin: 0 auto 20px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.brand-content h1 {
  font-size: 30px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 4px;
  margin-bottom: 8px;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
.brand-desc {
  color: rgba(255, 255, 255, 0.65);
  font-size: 13px;
  margin-bottom: 32px;
}
.brand-features {
  text-align: left;
  display: inline-block;
}
.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  margin-bottom: 14px;
}
.feature-item:last-child { margin-bottom: 0; }
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.6);
  flex-shrink: 0;
}

/* ── 右侧表单区 ── */
.form-side {
  flex: 1;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(24px);
  padding: 48px 44px 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.form-header {
  margin-bottom: 32px;
}
.form-header h2 {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 6px;
}
.form-header p {
  color: #94a3b8;
  font-size: 14px;
}

/* 输入框 */
.form-side :deep(.el-input__wrapper) {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  box-shadow: none;
  border-radius: 10px;
  height: 44px;
  transition: border-color 0.3s, box-shadow 0.3s;
}
.form-side :deep(.el-input__wrapper:hover) {
  border-color: #93c5fd;
}
.form-side :deep(.el-input__wrapper.is-focus) {
  border-color: #2EA9DF;
  box-shadow: 0 0 0 3px rgba(46, 169, 223, 0.1);
}
.form-side :deep(.el-input__prefix .el-icon) {
  color: #94a3b8;
}

.captcha-row {
  display: flex;
  gap: 12px;
  width: 100%;
}
.captcha-row .el-input { flex: 1; }
.captcha-canvas {
  height: 44px;
  border-radius: 10px;
  cursor: pointer;
  border: 1px solid #e2e8f0;
  flex-shrink: 0;
  transition: border-color 0.3s;
}
.captcha-canvas:hover {
  border-color: #93c5fd;
}

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 6px;
  background: linear-gradient(135deg, #2EA9DF, #238bbe);
  border: none;
  box-shadow: 0 4px 16px rgba(46, 169, 223, 0.3);
  transition: box-shadow 0.3s, transform 0.15s;
}
.login-btn:hover {
  box-shadow: 0 6px 24px rgba(46, 169, 223, 0.4);
  transform: translateY(-1px);
}
.login-btn:active {
  transform: translateY(0);
}

.form-footer {
  margin-top: 24px;
  text-align: center;
  color: #cbd5e1;
  font-size: 12px;
}

/* ── 移动端适配 ── */
@media (max-width: 768px) {
  .login-wrapper {
    width: calc(100% - 32px);
    min-height: auto;
    flex-direction: column;
    border-radius: 16px;
  }
  .brand-side {
    display: none;
  }
  .form-side {
    padding: 36px 24px 32px;
  }
  .form-header {
    margin-bottom: 24px;
  }
  .form-header h2 {
    font-size: 20px;
  }
  .captcha-row {
    gap: 8px;
  }
  .captcha-canvas {
    width: 100px;
    height: 40px;
  }
}

@media (max-width: 375px) {
  .form-side {
    padding: 28px 18px 24px;
  }
  .form-header h2 {
    font-size: 18px;
  }
}
</style>

import router from './index'
import { useUserStore } from '@/store/user'
import { useSiteStore } from '@/store/site'
import NProgress from 'nprogress'
import 'nprogress/nprogress.css'

NProgress.configure({ showSpinner: false })

const whitelist = ['/login']

router.beforeEach(async (to, from, next) => {
  NProgress.start()
  const userStore = useUserStore()
  const siteStore = useSiteStore()
  const token = userStore.token

  // Public routes (share page etc.) — but /login should redirect if already logged in
  if (to.path === '/login') {
    if (token) {
      next('/admin/dashboard')
      return
    }
    next()
    return
  }

  if (to.meta.public) {
    next()
    return
  }

  if (!token) {
    next(`/login?redirect=${to.path}`)
    return
  }

  // If we have token but no user info, fetch it
  if (!userStore.userInfo) {
    try {
      await userStore.fetchUserInfo()
      await userStore.fetchPermissions()
      if (!siteStore.loaded) await siteStore.loadSettings()
      next()
    } catch {
      userStore.logout()
      next(`/login?redirect=${to.path}`)
    }
    return
  }

  // Load site settings if not loaded yet
  if (!siteStore.loaded) {
    await siteStore.loadSettings()
  }

  next()
})

router.afterEach(() => {
  NProgress.done()
})

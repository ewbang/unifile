import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' },
  },
  {
    path: '/s/:code',
    name: 'ShareView',
    component: () => import('@/views/ShareView.vue'),
    meta: { title: '分享', public: true },
  },
  {
    path: '/',
    name: 'HomeView',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: '首页', public: true },
  },
  {
    path: '/admin',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/admin/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '控制台' },
      },
      {
        path: 'storages',
        name: 'Storages',
        component: () => import('@/views/Storages.vue'),
        meta: { title: '存储管理' },
      },
      {
        path: 'files/:id',
        name: 'Files',
        component: () => import('@/views/Files.vue'),
        meta: { title: '文件浏览' },
      },
      {
        path: 'shares',
        name: 'Shares',
        component: () => import('@/views/Shares.vue'),
        meta: { title: '分享管理' },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '站点设置' },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/Users.vue'),
        meta: { title: '用户管理' },
      },
      {
        path: 'roles',
        name: 'Roles',
        component: () => import('@/views/Roles.vue'),
        meta: { title: '角色管理' },
      },
      {
        path: 'menus',
        name: 'Menus',
        component: () => import('@/views/Menus.vue'),
        meta: { title: '菜单管理' },
      },
      {
        path: 'logs',
        name: 'Logs',
        component: () => import('@/views/Logs.vue'),
        meta: { title: '下载日志' },
      },
      {
        path: 'login-logs',
        name: 'LoginLogs',
        component: () => import('@/views/LoginLogs.vue'),
        meta: { title: '登录日志' },
      },
      {
        path: 'backups',
        name: 'Backups',
        component: () => import('@/views/Backups.vue'),
        meta: { title: '备份管理' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
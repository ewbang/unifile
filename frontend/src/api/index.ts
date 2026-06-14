import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Request interceptor — attach token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const url = error.config?.url || ''
    // 公开访问API（分享、首页）的401不跳转也不弹错误，由页面自行处理
    if (error.response?.status === 401 && (url.includes('/shares/access/') || url.includes('/home/'))) {
      return Promise.reject(error)
    }
    const msg = error.response?.data?.detail || error.message || '请求失败'
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
      return
    }
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default api

// ---- Auth API ----
export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  getMe: () => api.get('/auth/me'),
  getPermissions: () => api.get('/auth/permissions'),
  changePassword: (old_password: string, new_password: string) =>
    api.post('/auth/change-password', null, { params: { old_password, new_password } }),
}

// ---- Storage API ----
export const storageApi = {
  getTypes: () => api.get('/storages/types'),
  list: () => api.get('/storages/'),
  get: (id: number) => api.get(`/storages/${id}`),
  create: (data: any) => api.post('/storages/', data),
  update: (id: number, data: any) => api.put(`/storages/${id}`, data),
  delete: (id: number) => api.delete(`/storages/${id}`),
  testConnection: (id: number) => api.post(`/storages/${id}/test`),
  toggle: (id: number) => api.put(`/storages/${id}/toggle`),
  reorder: (items: { id: number; sort_order: number }[]) => api.post('/storages/reorder', items),
}

// ---- File API ----
export const fileApi = {
  list: (storageId: number, path: string = '/') =>
    api.get(`/files/${storageId}/list`, { params: { path } }),
  getInfo: (storageId: number, path: string) =>
    api.get(`/files/${storageId}/info`, { params: { path } }),
  getDownloadUrl: (storageId: number, path: string) =>
    api.get(`/files/${storageId}/download`, { params: { path } }),
  upload: (storageId: number, path: string, file: File, onProgress?: (e: any) => void) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/files/${storageId}/upload`, formData, {
      params: { path },
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress,
    })
  },
  deleteFile: (storageId: number, path: string) =>
    api.delete(`/files/${storageId}/file`, { params: { path } }),
  deleteFolder: (storageId: number, path: string) =>
    api.delete(`/files/${storageId}/folder`, { params: { path } }),
  mkdir: (storageId: number, path: string) =>
    api.post(`/files/${storageId}/mkdir`, null, { params: { path } }),
  move: (storageId: number, srcPath: string, destPath: string) =>
    api.post(`/files/${storageId}/move`, null, { params: { src_path: srcPath, dest_path: destPath } }),
  copy: (storageId: number, srcPath: string, destPath: string) =>
    api.post(`/files/${storageId}/copy`, null, { params: { src_path: srcPath, dest_path: destPath } }),
  search: (storageId: number, keyword: string, path: string = '/') =>
    api.get(`/files/${storageId}/search`, { params: { keyword, path } }),
  rename: (storageId: number, path: string, newName: string) =>
    api.post(`/files/${storageId}/rename`, null, { params: { path, new_name: newName } }),
  directLink: (storageId: number, path: string) =>
    api.get(`/files/${storageId}/direct-link`, { params: { path } }),
  previewUrl: (storageId: number, path: string) =>
    api.get(`/files/${storageId}/preview-url`, { params: { path } }),
  dirSize: (storageId: number, path: string) =>
    api.get(`/files/${storageId}/dir-size`, { params: { path } }),
}

// ---- Share API ----
export const shareApi = {
  create: (data: any) => api.post('/shares/', data),
  list: (params?: any) => api.get('/shares/', { params: params || {} }),
  update: (id: number, data: any) => api.put(`/shares/${id}`, data),
  delete: (id: number) => api.delete(`/shares/${id}`),
  toggle: (id: number) => api.put(`/shares/${id}/toggle`),
  batchDelete: (ids: number[]) => api.post('/shares/batch-delete', ids),
  access: (code: string, password?: string, subpath?: string) => {
    const params: any = {}
    if (password) params.password = password
    if (subpath) params.subpath = subpath
    return api.get(`/shares/access/${code}`, { params })
  },
}

// ---- Settings API ----
export const settingsApi = {
  get: () => api.get('/settings/'),
  update: (settings: Record<string, string>) => api.put('/settings/', { settings }),
  getPublic: () => api.get('/settings/public'),
}

// ---- Users API ----
export const usersApi = {
  list: () => api.get('/users/'),
  create: (data: any) => api.post('/users/', data),
  update: (id: number, data: any) => api.put(`/users/${id}`, data),
  delete: (id: number) => api.delete(`/users/${id}`),
  getMe: () => api.get('/users/me'),
  changePassword: (old_password: string, new_password: string) => api.put('/users/me/password', { old_password, new_password }),
}

// ---- Roles API ----
export const rolesApi = {
  list: () => api.get('/roles/'),
  create: (data: any) => api.post('/roles/', data),
  update: (id: number, data: any) => api.put(`/roles/${id}`, data),
  delete: (id: number) => api.delete(`/roles/${id}`),
  getMenus: () => api.get('/roles/menus'),
}

// ---- Menus API ----
export const menusApi = {
  list: () => api.get('/menus/'),
  create: (data: any) => api.post('/menus/', data),
  update: (id: number, data: any) => api.put(`/menus/${id}`, data),
  delete: (id: number) => api.delete(`/menus/${id}`),
}

// ---- Logs API ----
export const logsApi = {
  list: (params: any) => api.get('/logs/', { params }),
  stats: () => api.get('/logs/stats'),
  clear: () => api.delete('/logs/clear'),
}

// ---- Dashboard API ----
export const dashboardApi = {
  stats: () => api.get('/dashboard/stats'),
}

// ---- Login Logs API ----
export const loginLogsApi = {
  list: (params: any) => api.get('/login-logs/', { params }),
  stats: () => api.get('/login-logs/stats'),
  clear: () => api.delete('/login-logs/clear'),
}

// ---- Home Public API ----
export const homeApi = {
  getPublicStorages: () => api.get('/home/storages'),
  previewUrl: (storageId: number, path: string, password?: string) =>
    api.get(`/home/${storageId}/preview-url`, { params: { path, password } }),
  listFiles: (storageId: number, path: string = '/', password?: string) => {
    const params: any = { path }
    if (password) params.password = password
    return api.get(`/home/${storageId}/list`, { params })
  },
  downloadFile: (storageId: number, path: string, password?: string) => {
    const params: any = { path }
    if (password) params.password = password
    return api.get(`/home/${storageId}/download`, { params })
  },
  verifyPassword: (storageId: number, path: string, password: string) =>
    api.post(`/home/${storageId}/verify-password`, null, { params: { path, password } }),
}

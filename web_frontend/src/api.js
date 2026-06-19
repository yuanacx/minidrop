import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 30000,
  withCredentials: true,
})

export const getAgents = (target_ip = '127.0.0.1') =>
  api.get('/agents', { params: { target_ip } }).then((r) => r.data)

export const createTask = (body) => api.post('/tasks', body).then((r) => r.data)

export const listTasks = () => api.get('/tasks').then((r) => r.data)

/** GET /api/v1/tasks/:tid — 勿用 /tasks/result?tid= */
export const getTask = (tid) => api.get(`/tasks/${tid}`).then((r) => r.data)

export const runAnalyze = (tid) => api.post(`/tasks/${tid}/analyze`).then((r) => r.data)

/** MinIO 火焰图 / TopN（经 nginx /artifacts/ 反代） */
export const artifactUrl = (tid, name) => `/artifacts/${tid}/${name}`

export default api

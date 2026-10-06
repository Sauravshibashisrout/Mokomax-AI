import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const sendQuery = (payload) => api.post('/query', payload)
export const ingestDocument = (formData) =>
  api.post('/ingest', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
export const getEvalResults = () => api.get('/admin/eval')
export const triggerEval = (payload) => api.post('/admin/eval', payload)

export default api

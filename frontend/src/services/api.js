import axios from 'axios'

const API_BASE = '/api/v1'

// Helper to create axios instance with custom timeout
const createApiClient = (timeout = 30000) => {
  const client = axios.create({
    baseURL: API_BASE,
    timeout
  })
  
  // Error handler
  client.interceptors.response.use(
    response => response,
    error => {
      let message = 'Có lỗi xảy ra. Vui lòng thử lại!'
      
      if (error.code === 'ECONNABORTED') {
        message = '⏱️ Hết thời gian chờ. Vui lòng thử lại!'
      } else if (error.code === 'ERR_NETWORK') {
        message = '🌐 Lỗi kết nối. Kiểm tra server đang chạy không?'
      } else if (error.response) {
        if (error.response.status === 504) {
          message = '⏳ Server đang xử lý quá lâu. Vui lòng thử lại!'
        } else {
          message = `❌ Lỗi ${error.response.status}: Vui lòng thử lại!`
        }
      } else if (error.request) {
        message = '🔌 Không thể kết nối server. Kiểm tra kết nối internet!'
      }
      
      return Promise.reject(new Error(message))
    }
  )
  
  return client
}

// API clients
const api = createApiClient(30000)      // 30s for normal queries
const apiLong = createApiClient(300000) // 5 phút cho audio

// Retry 1 lần cho audio
apiLong.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config
    // Guard: error.config có thể undefined nếu lỗi xảy ra trước khi gửi request
    if (!originalRequest) {
      return Promise.reject(error)
    }
    if (!originalRequest._retryCount) {
      originalRequest._retryCount = 1
      console.log('Retrying audio request...')
      return apiLong(originalRequest)
    }
    return Promise.reject(error)
  }
)

// ============ EXPORTS ============

// Query RAG - qua LLM (có thể chậm)
export const queryRAG = async (query, userRole = 'patient', options = {}) => {
  const response = await api.post('/query', {
    query,
    user_role: userRole,
    ...options
  })
  return response.data
}

// Patient Chat
export const chatPatient = async (message, conversationId = null) => {
  const response = await api.post('/chat', {
    message,
    conversation_id: conversationId
  })
  return response.data
}

// Transcribe Audio — gửi qua backend proxy (Gemini STT → fallback PhoWhisper)
export const transcribeAudio = async (audioFile) => {
  console.log('[STT] Sending to backend (Gemini STT)...')
  const formData = new FormData()
  formData.append('file', audioFile, audioFile.name || 'audio.webm')

  const response = await apiLong.post('/speech/transcribe', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}


// Extract Medical Info
export const extractMedicalInfo = async (transcript, medicalRecord = '') => {
  const response = await apiLong.post('/speech/extract', {
    transcript,
    medical_record: medicalRecord
  })
  return response.data
}

// Retrieve Context - TRẢ THẲNG từ Vector DB (NHANH, không qua LLM)
export const retrieveContext = async (query, topK = 5, minSimilarity = 0.0) => {
  const response = await api.post('/retrieve', {
    query,
    top_k: topK,
    min_similarity: minSimilarity
  })
  return response.data
}

export default api
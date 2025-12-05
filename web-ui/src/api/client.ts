import axios, { AxiosError, AxiosRequestConfig } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

// Retry configuration
const MAX_RETRIES = 3
const INITIAL_RETRY_DELAY_MS = 1000
const MAX_RETRY_DELAY_MS = 10000

// HTTP status codes that should trigger a retry
const RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504]

// Track retry count per request
interface RetryConfig extends AxiosRequestConfig {
  __retryCount?: number
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

function getRetryDelay(retryCount: number): number {
  // Exponential backoff with jitter
  const delay = Math.min(
    INITIAL_RETRY_DELAY_MS * Math.pow(2, retryCount),
    MAX_RETRY_DELAY_MS
  )
  // Add 0-25% jitter to prevent thundering herd
  const jitter = delay * 0.25 * Math.random()
  return delay + jitter
}

function isRetryableError(error: AxiosError): boolean {
  // Network errors (no response)
  if (!error.response) {
    return true
  }
  // Retryable HTTP status codes
  return RETRYABLE_STATUS_CODES.includes(error.response.status)
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
})

// Request interceptor for adding auth token (if needed later)
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    // const token = localStorage.getItem('auth_token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor with retry logic
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryConfig

    if (!config) {
      return Promise.reject(error)
    }

    // Initialize retry count
    config.__retryCount = config.__retryCount || 0

    // Check if we should retry
    if (config.__retryCount < MAX_RETRIES && isRetryableError(error)) {
      config.__retryCount++

      const delay = getRetryDelay(config.__retryCount - 1)
      console.warn(
        `API request failed, retrying (${config.__retryCount}/${MAX_RETRIES}) after ${Math.round(delay)}ms:`,
        config.url
      )

      await sleep(delay)

      // Retry the request
      return apiClient.request(config)
    }

    // Log error after all retries exhausted
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.status, error.response.data)
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.message)
    } else {
      console.error('Error:', error.message)
    }

    return Promise.reject(error)
  }
)

export default apiClient

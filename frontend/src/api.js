/**
 * API Client for Medical RAG QA Backend
 * Handles all communication with the FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'; // Default to localhost:8000 for backend

/**
 * API Client class for backend communication
 */
class APIClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  /**
   * Make HTTP request
   * @param {string} endpoint - API endpoint path
   * @param {object} options - Fetch options
   * @returns {Promise} Response data
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    const fetchOptions = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, fetchOptions);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  /**
   * Health check endpoint
   * @returns {Promise} Health status
   */
  async healthCheck() {
    return this.request('/api/health');
  }

  /**
   * Ask a medical question
   * @param {string} question - Medical question
   * @param {string} mode - User mode: 'patient', 'doctor', or 'auto'
   * @returns {Promise} Medical answer response
   */
  async askQuestion(question, mode = 'auto') {
    return this.request('/api/ask', {
      method: 'POST',
      body: JSON.stringify({
        question,
        mode: mode.toLowerCase(),
      }),
    });
  }

  /**
   * Preprocess a query
   * @param {string} question - Medical question
   * @returns {Promise} Processed query with entities
   */
  async preprocessQuery(question) {
    return this.request('/api/preprocess', {
      method: 'POST',
      body: JSON.stringify({
        question,
        mode: 'auto',
      }),
    });
  }

  /**
   * Get system statistics
   * @returns {Promise} System statistics
   */
  async getStats() {
    return this.request('/api/stats');
  }
}

export const apiClient = new APIClient();

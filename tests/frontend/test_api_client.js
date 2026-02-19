/**
 * Frontend API client tests
 * These tests verify the functionality of the API client
 */

// Mock fetch API for testing
global.fetch = jest.fn();

describe('API Client Tests', () => {
  let apiClient;
  
  beforeEach(() => {
    // Reset fetch mock
    fetch.mockReset();
    
    // Import the API client
    apiClient = require('../../frontend/src/api.js').apiClient;
  });

  describe('healthCheck', () => {
    test('should return health data when successful', async () => {
      // Mock successful response
      const mockResponse = {
        status: 'healthy',
        version: '1.0.0',
        components: { preprocessor: 'ready' }
      };
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await apiClient.healthCheck();
      
      expect(result).toEqual(mockResponse);
      expect(fetch).toHaveBeenCalledWith(
        `${apiClient.baseURL}/api/health`,
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Content-Type': 'application/json'
          })
        })
      );
    });

    test('should throw error when request fails', async () => {
      fetch.mockResolvedValue({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error'
      });

      await expect(apiClient.healthCheck()).rejects.toThrow('HTTP 500');
    });
  });

  describe('askQuestion', () => {
    test('should send question to backend and return response', async () => {
      const mockQuestion = 'What is diabetes?';
      const mockResponse = {
        question: mockQuestion,
        answer: 'Diabetes is a condition...',
        confidence: 0.85
      };
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await apiClient.askQuestion(mockQuestion, 'patient');
      
      expect(result).toEqual(mockResponse);
      expect(fetch).toHaveBeenCalledWith(
        `${apiClient.baseURL}/api/ask`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            question: mockQuestion,
            mode: 'patient'
          })
        })
      );
    });

    test('should default to auto mode when no mode provided', async () => {
      const mockQuestion = 'What is diabetes?';
      const mockResponse = {
        question: mockQuestion,
        answer: 'Diabetes is a condition...',
        confidence: 0.85
      };
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await apiClient.askQuestion(mockQuestion);
      
      expect(fetch).toHaveBeenCalledWith(
        `${apiClient.baseURL}/api/ask`,
        expect.objectContaining({
          body: JSON.stringify({
            question: mockQuestion,
            mode: 'auto'
          })
        })
      );
    });
  });

  describe('preprocessQuery', () => {
    test('should send query to preprocessing endpoint', async () => {
      const mockQuestion = 'What is diabetes?';
      const mockResponse = {
        original_question: mockQuestion,
        entities: ['diabetes'],
        detected_mode: 'patient'
      };
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await apiClient.preprocessQuery(mockQuestion);
      
      expect(result).toEqual(mockResponse);
      expect(fetch).toHaveBeenCalledWith(
        `${apiClient.baseURL}/api/preprocess`,
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            question: mockQuestion,
            mode: 'auto'
          })
        })
      );
    });
  });

  describe('getStats', () => {
    test('should fetch system statistics', async () => {
      const mockResponse = {
        vector_store: { collection_count: 5000 },
        knowledge_graph: { nodes: 1000 }
      };
      
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await apiClient.getStats();
      
      expect(result).toEqual(mockResponse);
      expect(fetch).toHaveBeenCalledWith(
        `${apiClient.baseURL}/api/stats`,
        expect.objectContaining({
          method: 'GET'
        })
      );
    });
  });

  describe('request method', () => {
    test('should handle custom headers', async () => {
      const mockResponse = { data: 'test' };
      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockResponse
      });

      const result = await apiClient.request('/api/test', {
        method: 'POST',
        headers: { 'X-Custom-Header': 'test-value' }
      });

      expect(result).toEqual(mockResponse);
      expect(fetch).toHaveBeenCalledWith(
        `${apiClient.baseURL}/api/test`,
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            'X-Custom-Header': 'test-value'
          })
        })
      );
    });
  });
});
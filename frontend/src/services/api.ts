"""
API service client for Digital FTE AI Customer Success Agent frontend.
Handles communication with the backend API for form submissions and data retrieval.
"""

import axios from 'axios';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  [key: string]: any;
}

interface FormSubmissionData {
  name: string;
  email: string;
  subject: string;
  message: string;
}

interface SubmissionResponse {
  success: boolean;
  message: string;
  submissionId?: string;
  receivedAt?: string;
  [key: string]: any;
}

class ApiService {
  private baseURL: string;
  private axiosInstance: any;

  constructor(baseURL: string = '') {
    this.baseURL = baseURL.endsWith('/') ? baseURL.slice(0, -1) : baseURL;

    this.axiosInstance = axios.create({
      baseURL: this.baseURL,
      timeout: 10000, // 10 seconds timeout
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });

    // Add request interceptor for logging
    this.axiosInstance.interceptors.request.use(
      (config: any) => {
        // Add timestamp for debugging
        config.metadata = { ...config.metadata, startTime: new Date().toISOString() };
        return config;
      },
      (error: any) => {
        return Promise.reject(error);
      }
    );

    // Add response interceptor for logging and error handling
    this.axiosInstance.interceptors.response.use(
      (response: any) => {
        // Add response time
        if (response.config.metadata) {
          const endTime = new Date();
          const startTime = new Date(response.config.metadata.startTime);
          response.metadata = {
            ...response.config.metadata,
            endTime: endTime.toISOString(),
            responseTimeMs: endTime.getTime() - startTime.getTime()
          };
        }
        return response;
      },
      (error: any) => {
        // Handle network errors
        if (!error.response) {
          // Network error or timeout
          return Promise.reject({
            success: false,
            error: 'Network error. Please check your connection and try again.',
            isNetworkError: true
          });
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Submit a support form inquiry
   * @param formData Form data to submit
   * @returns Promise with submission response
   */
  async submitForm(formData: FormSubmissionData): Promise<ApiResponse<SubmissionResponse>> {
    try {
      const response = await this.axiosInstance.post<ApiResponse<SubmissionResponse>>(
        '/api/v1/inquiries/webform',
        formData
      );

      return response.data;
    } catch (error: any) {
      // Handle different types of errors
      if (error.response) {
        // Server responded with error status
        return {
          success: false,
          error: error.response.data?.error ||
                 error.response.data?.message ||
                 'Server error. Please try again later.',
          statusCode: error.response.status,
          serverError: true
        };
      } else if (error.request) {
        // Request was made but no response received
        return {
          success: false,
          error: 'No response from server. Please check your connection.',
          isNetworkError: true
        };
      } else {
        // Error setting up the request
        return {
          success: false,
          error: error.message || 'An unexpected error occurred',
          clientError: true
        };
      }
    }
  }

  /**
   * Check API health/status
   * @returns Promise with health check response
   */
  async checkHealth(): Promise<ApiResponse<any>> {
    try {
      const response = await this.axiosInstance.get<ApiResponse<any>>('/api/v1/inquiries/health');
      return response.data;
    } catch (error: any) {
      if (error.response) {
        return {
          success: false,
          error: error.response.data?.error || 'Service unavailable',
          statusCode: error.response.status
        };
      } else {
        return {
          success: false,
          error: 'Unable to reach service. Please check your connection.',
          isNetworkError: true
        };
      }
    }
  }

  /**
   * Get available resources or FAQ
   * @returns Promise with resources data
   */
  async getResources(): Promise<ApiResponse<any>> {
    try {
      const response = await this.axiosInstance.get<ApiResponse<any>>('/api/v1/resources/faq');
      return response.data;
    } catch (error: any) {
      if (error.response) {
        return {
          success: false,
          error: error.response.data?.error || 'Unable to load resources',
          statusCode: error.response.status
        };
      } else {
        return {
          success: false,
          error: 'Unable to load resources. Please check your connection.',
          isNetworkError: true
        };
      }
    }
  }

  /**
   * Update the base URL (useful for different environments)
   * @param baseURL New base URL for the API
   */
  setBaseURL(baseURL: string): void {
    this.baseURL = baseURL.endsWith('/') ? baseURL.slice(0, -1) : baseURL;
    this.axiosInstance.defaults.baseURL = this.baseURL;
  }

  /**
   * Get current base URL
   * @returns Current base URL
   */
  getBaseURL(): string {
    return this.baseURL;
  }
}

// Create a default instance for convenience
const apiService = new ApiService();

// Export both the class and the instance
export { ApiService, apiService };

// Export default for easy importing
export default apiService;
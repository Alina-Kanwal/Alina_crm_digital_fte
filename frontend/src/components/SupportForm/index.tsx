/**
 * Embeddable React/Next.js web support form for Digital FTE AI Customer Success Agent.
 * Provides a standalone, embeddable support form for customer inquiries with real-time response display.
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import apiService from '@/services/api';

interface SupportFormProps {
  /** Optional endpoint URL - defaults to relative API path */
  apiEndpoint?: string;
  /** Optional custom styling */
  className?: string;
  /** Optional title for the form */
  title?: string;
  /** Optional subtitle */
  subtitle?: string;
  /** Whether to show AI response preview */
  showResponsePreview?: boolean;
}

interface FormData {
  name: string;
  email: string;
  subject: string;
  message: string;
}

interface APIResponse {
  success: boolean;
  message: string;
  submissionId?: string;
  receivedAt?: string;
  aiResponse?: string;
  estimatedResponseTime?: string;
  [key: string]: any;
}

const SupportForm: React.FC<SupportFormProps> = ({
  apiEndpoint = '/api/v1/inquiries/webform',
  className = '',
  title = 'Need Help?',
  subtitle = 'Ask us anything about our product',
  showResponsePreview = true
}) => {
  const [formData, setFormData] = useState<FormData>({
    name: '',
    email: '',
    subject: '',
    message: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<{
    status: 'idle' | 'submitting' | 'success' | 'error';
    message: string;
  }>({ status: 'idle', message: '' });

  const [aiResponse, setAiResponse] = useState<string | null>(null);
  const [isCheckingResponse, setIsCheckingResponse] = useState(false);
  const [responseCheckInterval, setResponseCheckInterval] = useState<NodeJS.Timeout | null>(null);

  const [isValid, setIsValid] = useState<boolean>(false);

  // Validate form data
  useEffect(() => {
    const isValid =
      formData.name.trim().length >= 0 && // Name is optional
      formData.email.trim().length > 0 &&
      /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim()) && // Basic email validation
      formData.message.trim().length > 0;

    setIsValid(isValid);
  }, [formData]);

  // Check for AI response after submission
  useEffect(() => {
    if (submitStatus.status === 'success' && formData.email && showResponsePreview) {
      startCheckingForResponse();
    } else {
      stopCheckingForResponse();
    }
  }, [submitStatus.status, formData.email, showResponsePreview]);

  const startCheckingForResponse = () => {
    if (responseCheckInterval) return;

    setIsCheckingResponse(true);
    const interval = setInterval(checkForAIResponse, 3000); // Check every 3 seconds
    setResponseCheckInterval(interval);
  };

  const stopCheckingForResponse = () => {
    if (responseCheckInterval) {
      clearInterval(responseCheckInterval);
      setResponseCheckInterval(null);
    }
    setIsCheckingResponse(false);
  };

  const checkForAIResponse = async () => {
    try {
      // In a real implementation, this would check a dedicated endpoint
      // For demo purposes, we'll simulate an AI response after a delay
      // In production, this would poll an endpoint like:
      // /api/v1/inquiries/response/{submissionId}

      // Simulate checking for response
      await new Promise(resolve => setTimeout(resolve, 1000));

      // For now, we'll just show a placeholder response
      // In production, this would be replaced with actual AI response polling
      if (submitStatus.status === 'success') {
        setAiResponse(
          "Thank you for your inquiry! Our AI agent has received your message and is processing it. " +
          "You should receive a detailed response via email shortly. " +
          "If you need immediate assistance, please check your email for updates."
        );
        stopCheckingForResponse();  // Stop checking once we have a response
      }
    } catch (error) {
      console.error('Error checking for AI response:', error);
      // Continue checking despite errors
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isValid || isSubmitting) return;

    setIsSubmitting(true);
    setSubmitStatus({ status: 'submitting', message: 'Submitting your inquiry...' });
    setAiResponse(null);  // Clear previous response

    try {
      const response = await axios.post<APIResponse>(apiEndpoint, formData, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.data.success) {
        setSubmitStatus({
          status: 'success',
          message: response.data.message || 'Your inquiry has been submitted successfully!'
        });

        // Store submission ID for response tracking
        const submissionId = response.data.submissionId ||
                           `${formData.email}_${Date.now()}`;

        // Reset form after successful submission
        setFormData({
          name: '',
          email: '',
          subject: '',
          message: ''
        });

        // Start checking for AI response if enabled
        if (showResponsePreview) {
          setIsCheckingResponse(true);
        }
      } else {
        throw new Error(response.data.message || 'Submission failed');
      }
    } catch (error: any) {
      console.error('Error submitting form:', error);
      setSubmitStatus({
        status: 'error',
        message: error.response?.data?.message ||
                 error.message ||
                 'Failed to submit inquiry. Please try again.'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={`digital-fte-support-form ${className}`}>
      <div className="support-form-container">
        <h2 className="support-form-title">{title}</h2>
        <p className="support-form-subtitle">{subtitle}</p>

        <form onSubmit={handleSubmit} className="support-form">
          <div className="form-group">
            <label htmlFor="name">Your Name (Optional)</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="Enter your name"
              className="form-input"
              autoComplete="name"
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">Email Address *</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter your email address"
              className="form-input"
              required
              autoComplete="email"
            />
            <p className="form-help">We'll use this to respond to your inquiry</p>
          </div>

          <div className="form-group">
            <label htmlFor="subject">Subject (Optional)</label>
            <input
              type="text"
              id="subject"
              name="subject"
              value={formData.subject}
              onChange={handleChange}
              placeholder="Briefly describe your inquiry"
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="message">Your Message *</label>
            <textarea
              id="message"
              name="message"
              value={formData.message}
              onChange={handleChange}
              rows={5}
              placeholder="Please describe your question or issue in detail"
              className="form-textarea"
              required
            />
            <p className="form-help">
              Please avoid sharing sensitive information like passwords or credit card numbers
            </p>
          </div>

          <button
            type="submit"
            disabled={!isValid || isSubmitting}
            className={`submit-button ${isSubmitting ? 'submitting' : ''}`}
          >
            {isSubmitting ? 'Submitting...' : 'Send Message'}
          </button>
        </form>

        {submitStatus.status !== 'idle' && (
          <div className={`submit-status ${submitStatus.status}`}>
            {submitStatus.message}
          </div>
        )}

        {showResponsePreview && isCheckingResponse && (
          <div className="response-status checking">
            <div className="spinner"></div>
            <p>Checking for AI response...</p>
          </div>
        )}

        {showResponsePreview && aiResponse && (
          <div className="ai-response-panel">
            <h3>AI Response Preview</h3>
            <p className="ai-response-text">{aiResponse}</p>
            <p className="ai-response-note">
              *This is a preview. The full response will be sent to your email.
            </p>
          </div>
        )}

        {showResponsePreview && submitStatus.status === 'success' && !aiResponse && !isCheckingResponse && (
          <div className="response-status info">
            <p>Checking for AI response... (this may take a moment)</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SupportForm;
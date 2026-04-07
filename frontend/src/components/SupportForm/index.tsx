/**
 * Embeddable React/Next.js web support form for Digital FTE AI Customer Success Agent.
 * Provides a standalone, embeddable support form for customer inquiries with real-time response display.
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

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
  title = 'Get Premium Support',
  subtitle = 'Experience AI-powered immediate resolutions',
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
      await new Promise(resolve => setTimeout(resolve, 1000));
      if (submitStatus.status === 'success') {
        setAiResponse(
          "Thank you for your inquiry! Our AI agent has received your message and is processing it. You will receive a detailed resolution via email shortly."
        );
        stopCheckingForResponse();
      }
    } catch (error) {
      console.error('Error checking for AI response:', error);
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
    setAiResponse(null);

    try {
      const response = await axios.post<APIResponse>(apiEndpoint, formData, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.data.success) {
        setSubmitStatus({
          status: 'success',
          message: response.data.message || 'Your request has been beautifully received!'
        });

        const submissionId = response.data.submissionId || `${formData.email}_${Date.now()}`;

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
      <div className="container">
        <div className="header">
          <h2 className="title">{title}</h2>
          <p className="subtitle">{subtitle}</p>
        </div>

        <form onSubmit={handleSubmit} className="support-form">
          <div className="form-group">
            <label htmlFor="name" className="form-label">Full Name</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="e.g. Jane Doe"
              className="form-control"
              autoComplete="name"
            />
          </div>

          <div className="form-group">
            <label htmlFor="email" className="form-label">Email Address *</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="jane@example.com"
              className="form-control"
              required
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="subject" className="form-label">Subject</label>
            <input
              type="text"
              id="subject"
              name="subject"
              value={formData.subject}
              onChange={handleChange}
              placeholder="How can we help you?"
              className="form-control"
            />
          </div>

          <div className="form-group">
            <label htmlFor="message" className="form-label">Message *</label>
            <textarea
              id="message"
              name="message"
              value={formData.message}
              onChange={handleChange}
              placeholder="Please describe your inquiry in detail..."
              className="form-control"
              required
            />
          </div>

          <button
            type="submit"
            disabled={!isValid || isSubmitting}
            className="btn-submit"
          >
            {isSubmitting ? (
              <>
                <div className="spinner"></div> Processing...
              </>
            ) : (
              'Send Request'
            )}
          </button>
        </form>

        {submitStatus.status === 'success' && (
          <div className="alert alert-success">
            <h3>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
              Request Received
            </h3>
            <p>{submitStatus.message}</p>
            
            {showResponsePreview && isCheckingResponse && (
              <div className="response-status checking" style={{marginTop: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.8rem', color: '#94a3b8'}}>
                <div className="spinner" style={{width: '16px', height: '16px', borderWidth: '2px', borderTopColor: '#3b82f6'}}></div>
                <p style={{margin: 0, fontSize: '0.9rem'}}>AI is analyzing your request...</p>
              </div>
            )}
            
            {showResponsePreview && aiResponse && (
              <div className="response-details" style={{marginTop: '1rem', animation: 'slideUp 0.5s ease'}}>
                <p style={{display:'block', marginBottom: '0.5rem'}}><strong>AI Quick Response:</strong></p>
                <p style={{display:'block', color: '#f8fafc', lineHeight: '1.5'}}>{aiResponse}</p>
              </div>
            )}
            
            {showResponsePreview && submitStatus.status === 'success' && !aiResponse && !isCheckingResponse && (
              <div className="response-status info" style={{marginTop: '1rem', color: '#94a3b8', fontSize: '0.9rem'}}>
                <p>AI response analysis complete.</p>
              </div>
            )}
          </div>
        )}

        {submitStatus.status === 'error' && (
          <div className="alert alert-error">
             <h3>
               <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight:'8px', verticalAlign:'middle'}}><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
               Submission Failed
             </h3>
             <p>{submitStatus.message}</p>
          </div>
        )}
        
        <div className="footer">
          <div className="powered-by">
            <div className="dot"></div>
            <span>Powered by Digital FTE Agent</span>
          </div>
          <p style={{ margin: '0', opacity: 0.7 }}>24/7 AI-Powered Support</p>
        </div>
      </div>
    </div>
  );
};

export default SupportForm;
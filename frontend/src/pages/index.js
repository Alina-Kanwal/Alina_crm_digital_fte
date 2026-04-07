import Head from 'next/head';
import { useState } from 'react';

export default function Home() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: ''
  });

  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResponse(null);

    try {
      const backendResponse = await fetch('http://localhost:8000/api/v1/inquiries', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          channel: 'webform',
          subject: formData.subject,
          description: formData.message,
          customer_info: {
            name: formData.name,
            email: formData.email
          }
        })
      });

      const result = await backendResponse.json();
      setResponse({
        success: true,
        data: result
      });
    } catch (error) {
      setResponse({
        success: false,
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Digital FTE Agent - Web Support Form</title>
        <meta name="description" content="Embeddable web support form for Digital FTE AI Customer Success Agent" />
      </Head>

      <div className="bg-blobs">
        <div className="blob blob-1"></div>
        <div className="blob blob-2"></div>
        <div className="blob blob-3"></div>
      </div>

      <main className="container">
        <div className="header">
          <h1 className="title">Get Premium Support</h1>
          <p className="subtitle">Experience AI-powered immediate resolutions</p>
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
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email" className="form-label">Email Address</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="jane@example.com"
              className="form-control"
              required
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
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="message" className="form-label">Message</label>
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
            disabled={loading}
            className="btn-submit"
          >
            {loading ? (
              <>
                <div className="spinner"></div> Processing...
              </>
            ) : (
              'Send Request'
            )}
          </button>
        </form>

        {response && (
          <div className={`alert ${response.success ? 'alert-success' : 'alert-error'}`}>
            {response.success ? (
              <>
                <h3>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                  Request Received
                </h3>
                <p>Our intelligent AI agent is already looking into your request.</p>
                {response.data && (
                  <div className="response-details">
                    <p><strong>Tracking ID:</strong> <span>{response.data.id || 'N/A'}</span></p>
                    <p><strong>Channel:</strong> <span>{response.data.channel || 'webform'}</span></p>
                    <p><strong>Status:</strong> <span style={{ color: '#34d399' }}>Processing In-Progress</span></p>
                  </div>
                )}
              </>
            ) : (
              <>
                <h3>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight:'8px', verticalAlign:'middle'}}><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
                  Submission Failed
                </h3>
                <p>{response.error}</p>
              </>
            )}
          </div>
        )}

        <div className="footer">
          <div className="powered-by">
            <div className="dot"></div>
            <span>Powered by Digital FTE Agent</span>
          </div>
          <p style={{ margin: '0', opacity: 0.7 }}>24/7 AI-Powered Support</p>
        </div>
      </main>
    </>
  );
}
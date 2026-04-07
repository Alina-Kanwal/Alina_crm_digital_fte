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
      // Send the form data to our backend API
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
    <div>
      <Head>
        <title>Digital FTE Agent - Web Support Form</title>
        <meta name="description" content="Embeddable web support form for Digital FTE AI Customer Success Agent" />
      </Head>

      <main style={{
        maxWidth: '600px',
        margin: '2rem auto',
        padding: '2rem',
        fontFamily: 'system-ui, sans-serif'
      }}>
        <h1 style={{
          textAlign: 'center',
          color: '#2563eb',
          marginBottom: '2rem'
        }}>
          Digital FTE Agent Support
        </h1>

        <p style={{
          textAlign: 'center',
          color: '#6b7280',
          marginBottom: '2rem'
        }}>
          Get AI-powered support for your questions and issues
        </p>

        <form onSubmit={handleSubmit} style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '1rem'
        }}>
          <div>
            <label htmlFor="name" style={{
              display: 'block',
              marginBottom: '0.5rem',
              fontWeight: 'bold'
            }}>
              Name
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #d1d5db',
                borderRadius: '0.5rem',
                fontSize: '1rem'
              }}
            />
          </div>

          <div>
            <label htmlFor="email" style={{
              display: 'block',
              marginBottom: '0.5rem',
              fontWeight: 'bold'
            }}>
              Email
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #d1d5db',
                borderRadius: '0.5rem',
                fontSize: '1rem'
              }}
            />
          </div>

          <div>
            <label htmlFor="subject" style={{
              display: 'block',
              marginBottom: '0.5rem',
              fontWeight: 'bold'
            }}>
              Subject
            </label>
            <input
              type="text"
              id="subject"
              name="subject"
              value={formData.subject}
              onChange={handleChange}
              required
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #d1d5db',
                borderRadius: '0.5rem',
                fontSize: '1rem'
              }}
            />
          </div>

          <div>
            <label htmlFor="message" style={{
              display: 'block',
              marginBottom: '0.5rem',
              fontWeight: 'bold'
            }}>
              Message
            </label>
            <textarea
              id="message"
              name="message"
              value={formData.message}
              onChange={handleChange}
              rows="6"
              required
              style={{
                width: '100%',
                padding: '0.75rem',
                border: '1px solid #d1d5db',
                borderRadius: '0.5rem',
                fontSize: '1rem',
                resize: 'vertical'
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              backgroundColor: '#2563eb',
              color: 'white',
              border: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '0.5rem',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
              transition: 'all 0.2s ease'
            }}
          >
            {loading ? 'Sending...' : 'Send Message'}
          </button>
        </form>

        {response && (
          <div style={{
            marginTop: '2rem',
            padding: '1.5rem',
            borderRadius: '0.5rem',
            textAlign: 'center'
          }}>
            {response.success ? (
              <div style={{
                backgroundColor: '#dcfce7',
                color: '#166534',
                border: '1px solid #bbf7d0'
              }}>
                <h3>✅ Message Sent Successfully!</h3>
                <p>Our AI agent will process your inquiry and respond shortly.</p>
                {response.data && (
                  <div style={{
                    marginTop: '1rem',
                    fontSize: '0.9rem',
                    color: '#374151'
                  }}>
                    <p><strong>Response ID:</strong> {response.data.id || 'N/A'}</p>
                    <p><strong>Channel:</strong> {response.data.channel || 'webform'}</p>
                    <p><strong>Timestamp:</strong> {response.data.timestamp || 'Just now'}</p>
                  </div>
                )}
              </div>
            ) : (
              <div style={{
                backgroundColor: '#fef2f2',
                color: '#991b1b',
                border: '1px solid #fecaca'
              }}>
                <h3>❌ Error Sending Message</h3>
                <p>{response.error}</p>
              </div>
            )}
          </div>
        )}

        <div style={{
          marginTop: '2rem',
          paddingTop: '2rem',
          borderTop: '1px solid #e5e7eb',
          textAlign: 'center',
          color: '#9ca3af',
          fontSize: '0.9rem'
        }}>
          <p>Powered by Digital FTE Agent AI Customer Success Agent</p>
          <p><small>Version 1.0.0 | AI-Powered Support 24/7</small></p>
        </div>
      </main>
    </div>
  );
}
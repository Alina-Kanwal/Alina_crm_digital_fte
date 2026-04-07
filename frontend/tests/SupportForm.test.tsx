/**
 * Jest tests for SupportForm component.
 * Tests embeddable React/Next.js web support form.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import SupportForm from '../src/components/SupportForm';

// Mock API service
jest.mock('../src/services/api', () => ({
  submitInquiry: jest.fn(),
}));

// Mock form validation library
jest.mock('zod', () => ({
  z: {
    object: jest.fn(),
    string: jest.fn(),
    email: jest.fn(),
    min: jest.fn(),
  },
}));

describe('SupportForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders form with all required fields', () => {
    render(<SupportForm />);

    // Check for name field
    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();

    // Check for email field
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();

    // Check for message field
    expect(screen.getByLabelText(/message/i)).toBeInTheDocument();

    // Check for submit button
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
  });

  test('shows validation error for empty required fields', async () => {
    render(<SupportForm />);

    // Try to submit without filling fields
    const submitButton = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(submitButton);

    // Wait for validation errors
    await waitFor(() => {
      expect(screen.getByText(/name is required/i)).toBeInTheDocument();
      expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      expect(screen.getByText(/message is required/i)).toBeInTheDocument();
    });
  });

  test('shows validation error for invalid email format', async () => {
    render(<SupportForm />);

    // Enter invalid email
    const emailInput = screen.getByLabelText(/email/i);
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(submitButton);

    // Wait for validation error
    await waitFor(() => {
      expect(screen.getByText(/invalid email format/i)).toBeInTheDocument();
    });
  });

  test('shows validation error for message that is too short', async () => {
    render(<SupportForm />);

    // Fill valid name and email
    fireEvent.change(screen.getByLabelText(/name/i), { target: { value: 'John Doe' } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });

    // Enter message that is too short
    const messageInput = screen.getByLabelText(/message/i);
    fireEvent.change(messageInput, { target: { value: 'Hi' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(submitButton);

    // Wait for validation error
    await waitFor(() => {
      expect(screen.getByText(/message must be at least 10 characters/i)).toBeInTheDocument();
    });
  });

  test('submits form successfully with valid data', async () => {
    const { submitInquiry } = require('../src/services/api');
    submitInquiry.mockResolvedValue({
      success: true,
      ticket_id: 'TICKET-123',
      message: 'Inquiry submitted successfully',
    });

    render(<SupportForm />);

    // Fill form with valid data
    fireEvent.change(screen.getByLabelText(/name/i), { target: { value: 'Jane Smith' } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'jane@example.com' } });
    fireEvent.change(screen.getByLabelText(/message/i), { target: { value: 'I need help with my integration setup' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(submitButton);

    // Wait for submission
    await waitFor(() => {
      expect(submitInquiry).toHaveBeenCalledWith({
        channel: 'webform',
        customer_email: 'jane@example.com',
        customer_name: 'Jane Smith',
        message: 'I need help with my integration setup',
        session_id: expect.any(String),
      });
    });

    // Verify success message
    expect(screen.getByText(/inquiry submitted successfully/i)).toBeInTheDocument();
  });

  test('displays error message when submission fails', async () => {
    const { submitInquiry } = require('../src/services/api');
    submitInquiry.mockRejectedValue({
      response: {
        data: {
          error: 'Server error',
        },
      },
    });

    render(<SupportForm />);

    // Fill form with valid data
    fireEvent.change(screen.getByLabelText(/name/i), { target: { value: 'John Doe' } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'john@example.com' } });
    fireEvent.change(screen.getByLabelText(/message/i), { target: { value: 'Test message that is long enough' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(submitButton);

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/submission failed/i)).toBeInTheDocument();
    });
  });

  test('disables submit button while submitting', async () => {
    const { submitInquiry } = require('../src/services/api');
    // Simulate slow API call
    submitInquiry.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ success: true }), 2000))
    );

    render(<SupportForm />);

    // Fill form
    fireEvent.change(screen.getByLabelText(/name/i), { target: { value: 'Test User' } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/message/i), { target: { value: 'Test message for submission' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /submit/i });
    fireEvent.click(submitButton);

    // Verify button is disabled during submission
    expect(submitButton).toBeDisabled();
    expect(screen.getByText(/submitting/i)).toBeInTheDocument();

    // Wait for submission to complete
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled();
    }, { timeout: 3000 });
  });

  test('handles long messages appropriately', async () => {
    const { submitInquiry } = require('../src/services/api');
    submitInquiry.mockResolvedValue({ success: true, ticket_id: 'TICKET-456' });

    render(<SupportForm />);

    // Enter very long message
    const longMessage = 'This is a very long message. ' * 100;
    fireEvent.change(screen.getByLabelText(/name/i), { target: { value: 'Test User' } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    const messageInput = screen.getByLabelText(/message/i);

    // Type long message
    fireEvent.change(messageInput, { target: { value: longMessage } });

    // Check character count display
    expect(screen.getByText(/character count/i)).toBeInTheDocument();

    // Verify message is truncated if too long
    const currentMessage = messageInput.getAttribute('value');
    expect(currentMessage.length).toBeLessThanOrEqual(5000);
  });

  test('resets form after successful submission', async () => {
    const { submitInquiry } = require('../src/services/api');
    submitInquiry.mockResolvedValue({
      success: true,
      ticket_id: 'TICKET-789',
      message: 'Success',
    });

    render(<SupportForm />);

    // Fill form
    const nameInput = screen.getByLabelText(/name/i);
    const emailInput = screen.getByLabelText(/email/i);
    const messageInput = screen.getByLabelText(/message/i);

    fireEvent.change(nameInput, { target: { value: 'John Doe' } });
    fireEvent.change(emailInput, { target: { value: 'john@example.com' } });
    fireEvent.change(messageInput, { target: { value: 'Test message' } });

    // Submit form
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for form reset
    await waitFor(() => {
      expect(nameInput.value).toBe('');
      expect(emailInput.value).toBe('');
      expect(messageInput.value).toBe('');
    });
  });

  test('allows user to clear form manually', () => {
    render(<SupportForm />);

    // Fill form
    fireEvent.change(screen.getByLabelText(/name/i), { target: { value: 'John Doe' } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'john@example.com' } });
    fireEvent.change(screen.getByLabelText(/message/i), { target: { value: 'Test message' } });

    // Click clear button
    const clearButton = screen.getByRole('button', { name: /clear/i });
    fireEvent.click(clearButton);

    // Verify form is cleared
    expect(screen.getByLabelText(/name/i)).toHaveValue('');
    expect(screen.getByLabelText(/email/i)).toHaveValue('');
    expect(screen.getByLabelText(/message/i)).toHaveValue('');
  });

  test('displays real-time validation feedback', () => {
    render(<SupportForm />);

    const emailInput = screen.getByLabelText(/email/i);

    // Enter invalid email
    fireEvent.change(emailInput, { target: { value: 'invalid' } });

    // Should show validation error immediately
    expect(screen.getByText(/invalid email/i)).toBeInTheDocument();

    // Fix email
    fireEvent.change(emailInput, { target: { value: 'valid@example.com' } });

    // Validation error should disappear
    expect(screen.queryByText(/invalid email/i)).not.toBeInTheDocument();
  });

  test('supports session ID for cross-channel tracking', async () => {
    const { submitInquiry } = require('../src/services/api');
    submitInquiry.mockResolvedValue({ success: true, ticket_id: 'TICKET-101' });

    render(<SupportForm sessionId="session-xyz-123" />);

    // Fill and submit form
    fireEvent.change(screen.getByLabelText(/name/i), { target: { value: 'Test User' } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/message/i), { target: { value: 'Test message' } });

    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(submitInquiry).toHaveBeenCalledWith(
        expect.objectContaining({
          session_id: 'session-xyz-123',
        })
      );
    });
  });

  test('is accessible via keyboard navigation', () => {
    render(<SupportForm />);

    const nameInput = screen.getByLabelText(/name/i);
    const emailInput = screen.getByLabelText(/email/i);
    const messageInput = screen.getByLabelText(/message/i);
    const submitButton = screen.getByRole('button', { name: /submit/i });

    // Verify elements are focusable
    expect(nameInput).toHaveFocus();
    nameInput.blur();

    emailInput.focus();
    expect(emailInput).toHaveFocus();
    emailInput.blur();

    messageInput.focus();
    expect(messageInput).toHaveFocus();
    messageInput.blur();

    submitButton.focus();
    expect(submitButton).toHaveFocus();
  });

  test('displays loading spinner during submission', async () => {
    const { submitInquiry } = require('../src/services/api');
    submitInquiry.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ success: true }), 1000))
    );

    render(<SupportForm />);

    // Fill and submit form
    fireEvent.change(screen.getByLabelText(/name/i), { target: { value: 'Test User' } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/message/i), { target: { value: 'Test message' } });

    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Check for loading spinner
    await waitFor(() => {
      expect(screen.getByRole('status')).toBeInTheDocument();
      expect(screen.getByText(/loading/i) || screen.getByText(/submitting/i)).toBeInTheDocument();
    });
  });

  test('handles network errors gracefully', async () => {
    const { submitInquiry } = require('../src/services/api');
    submitInquiry.mockRejectedValue(new Error('Network Error'));

    render(<SupportForm />);

    // Fill and submit form
    fireEvent.change(screen.getByLabelText(/name/i), { target: { value: 'Test User' } });
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/message/i), { target: { value: 'Test message' } });

    fireEvent.click(screen.getByRole('button', { name: /submit/i }));

    // Wait for error message
    await waitFor(() => {
      expect(screen.getByText(/network error|connection failed/i)).toBeInTheDocument();
    });
  });
});

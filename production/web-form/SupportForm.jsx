// production/web-form/SupportForm.jsx
import React, { useState } from 'react';

const CATEGORIES = [
  { value: 'general', label: 'General Question' },
  { value: 'technical', label: 'Technical Support' },
  { value: 'billing', label: 'Billing Inquiry' },
  { value: 'bug_report', label: 'Bug Report' },
  { value: 'feedback', label: 'Feedback' }
];

export default function SupportForm({ apiEndpoint = '/support/submit' }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    category: 'general',
    message: ''
  });
  const [status, setStatus] = useState('idle'); // 'idle', 'submitting', 'success', 'error'
  const [ticketId, setTicketId] = useState(null);
  const [error, setError] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('submitting');
    setError(null);

    try {
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      if (!response.ok) throw new Error('Submission failed');

      const data = await response.json();
      setTicketId(data.ticket_id);
      setStatus('success');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  };

  if (status === 'success') {
    return (
      <div className="p-6 bg-white rounded shadow">
        <h2 className="text-xl font-bold mb-4">Thank You!</h2>
        <p>Your ticket has been created: <strong>{ticketId}</strong></p>
        <button 
          onClick={() => setStatus('idle')}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded"
        >
          Submit Another
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-6 bg-white rounded shadow">
      <h2 className="text-xl font-bold mb-4">Contact Support</h2>
      {error && <p className="text-red-500">{error}</p>}
      
      <div>
        <label className="block mb-1">Name</label>
        <input type="text" name="name" required onChange={handleChange} className="w-full border p-2 rounded" />
      </div>

      <div>
        <label className="block mb-1">Email</label>
        <input type="email" name="email" required onChange={handleChange} className="w-full border p-2 rounded" />
      </div>

      <div>
        <label className="block mb-1">Subject</label>
        <input type="text" name="subject" required onChange={handleChange} className="w-full border p-2 rounded" />
      </div>

      <div>
        <label className="block mb-1">Category</label>
        <select name="category" onChange={handleChange} className="w-full border p-2 rounded">
          {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.label}</option>)}
        </select>
      </div>

      <div>
        <label className="block mb-1">Message</label>
        <textarea name="message" required onChange={handleChange} className="w-full border p-2 rounded" rows="4"></textarea>
      </div>

      <button 
        type="submit" 
        disabled={status === 'submitting'}
        className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
      >
        {status === 'submitting' ? 'Submitting...' : 'Send Message'}
      </button>
    </form>
  );
}

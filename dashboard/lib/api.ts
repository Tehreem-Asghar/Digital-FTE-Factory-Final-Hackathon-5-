const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function fetchApi(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new Error(error.detail || response.statusText);
  }

  return response.json();
}

export const api = {
  getTickets: () => fetchApi('/api/tickets'),
  getTicketDetails: (ticketId: string) => fetchApi(`/api/tickets/${ticketId}`),
  getCustomers: () => fetchApi('/api/customers'),
  getCustomerDetails: (customerId: string) => fetchApi(`/api/customers/${customerId}`),
  getConversations: () => fetchApi('/api/conversations'),
  getMessages: (conversationId: string) => fetchApi(`/api/conversations/${conversationId}/messages`),
  getDashboardStats: () => fetchApi('/api/dashboard/stats'),
  submitSupport: (data: any) => fetchApi('/support/submit', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  submitEmail: (data: any) => fetchApi('/support/email', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  submitWhatsApp: (data: any) => fetchApi('/support/whatsapp', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  getMetricsSummary: () => fetchApi('/metrics/summary'),
  getMetricsChannels: () => fetchApi('/metrics/channels'),
};

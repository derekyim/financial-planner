/**
 * Chat Service
 * Handles communication with the backend chat API
 */

// Use relative URL in production (same domain), localhost in development
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 
  (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

type ChatResponse = {
  reply: string;
};

type HealthResponse = {
  status: string;
};

/**
 * Send a message to the chat API and get a response
 * @param message - The user's message to send
 * @returns The AI's reply
 */
async function sendMessage(message: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to send message');
  }

  const data: ChatResponse = await response.json();
  return data.reply;
}

/**
 * Check if the API is healthy and reachable
 * @returns True if the API is healthy
 */
async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/`);
    if (!response.ok) return false;
    
    const data: HealthResponse = await response.json();
    return data.status === 'ok';
  } catch {
    return false;
  }
}

export const chatService = {
  sendMessage,
  checkHealth,
};


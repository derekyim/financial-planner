const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ||
  (typeof window !== 'undefined' && window.location.hostname !== 'localhost' ? '' : 'http://localhost:8000');

type ChatResponse = { reply: string };
type HealthResponse = { status: string };

export type StreamCallbacks = {
  onThinking?: (text: string) => void;
  onLog?: (text: string) => void;
  onReply?: (text: string) => void;
  onError?: (text: string) => void;
};

async function sendMessage(message: string, threadId?: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, thread_id: threadId }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to send message');
  }

  const data: ChatResponse = await response.json();
  return data.reply;
}

async function sendMessageStream(
  message: string,
  callbacks: StreamCallbacks,
  threadId?: string,
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, thread_id: threadId }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to send message');
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No response stream');

  const decoder = new TextDecoder();
  let buffer = '';
  let finalReply = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';

    let currentEvent = '';
    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim();
      } else if (line.startsWith('data: ') && currentEvent) {
        try {
          const data = JSON.parse(line.slice(6));
          switch (currentEvent) {
            case 'thinking':
              callbacks.onThinking?.(data.text);
              break;
            case 'log':
              callbacks.onLog?.(data.text);
              break;
            case 'reply':
              finalReply = data.text;
              callbacks.onReply?.(data.text);
              break;
            case 'error':
              callbacks.onError?.(data.text);
              break;
          }
        } catch { /* skip malformed JSON */ }
        currentEvent = '';
      } else if (line === '') {
        currentEvent = '';
      }
    }
  }

  return finalReply;
}

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
  sendMessageStream,
  checkHealth,
};


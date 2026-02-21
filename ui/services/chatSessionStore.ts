export type ChatSession = {
  id: string;
  title: string;
  messages: {
    id: string;
    text: string;
    isUser: boolean;
    timestamp: Date;
  }[];
  updatedAt: Date;
};

const STORAGE_KEY = 'fp-chat-sessions';

type Listener = () => void;

let _sessions: ChatSession[] = [];
let _listeners: Listener[] = [];

function hydrateFromStorage(): ChatSession[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as ChatSession[];
    return parsed.map((s) => ({
      ...s,
      updatedAt: new Date(s.updatedAt),
      messages: s.messages.map((m) => ({ ...m, timestamp: new Date(m.timestamp) })),
    }));
  } catch {
    return [];
  }
}

function persistToStorage() {
  if (typeof window === 'undefined') return;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(_sessions));
  } catch {
    /* quota exceeded — silently drop */
  }
}

function notify() {
  _listeners.forEach((fn) => fn());
}

_sessions = hydrateFromStorage();

export const chatSessionStore = {
  getAll(): ChatSession[] {
    return [..._sessions].sort(
      (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
    );
  },

  get(id: string): ChatSession | undefined {
    return _sessions.find((s) => s.id === id);
  },

  save(session: ChatSession) {
    const idx = _sessions.findIndex((s) => s.id === session.id);
    if (idx >= 0) {
      _sessions = [..._sessions];
      _sessions[idx] = session;
    } else {
      _sessions = [..._sessions, session];
    }
    persistToStorage();
    notify();
  },

  remove(id: string) {
    _sessions = _sessions.filter((s) => s.id !== id);
    persistToStorage();
    notify();
  },

  clear() {
    _sessions = [];
    persistToStorage();
    notify();
  },

  subscribe(listener: Listener): () => void {
    _listeners = [..._listeners, listener];
    return () => {
      _listeners = _listeners.filter((fn) => fn !== listener);
    };
  },
};

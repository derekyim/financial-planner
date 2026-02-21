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

type Listener = () => void;

let _sessions: ChatSession[] = [];
let _listeners: Listener[] = [];

function notify() {
  _listeners.forEach((fn) => fn());
}

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
    notify();
  },

  remove(id: string) {
    _sessions = _sessions.filter((s) => s.id !== id);
    notify();
  },

  clear() {
    _sessions = [];
    notify();
  },

  subscribe(listener: Listener): () => void {
    _listeners = [..._listeners, listener];
    return () => {
      _listeners = _listeners.filter((fn) => fn !== listener);
    };
  },
};

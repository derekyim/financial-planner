export type LogEntry = {
  id: string;
  timestamp: Date;
  source: 'SERVER' | 'UI';
  text: string;
};

type Listener = () => void;

let _logs: LogEntry[] = [];
let _listeners: Listener[] = [];
let _nextId = 0;

function notify() {
  _listeners.forEach((fn) => fn());
}

export const logStore = {
  add(source: LogEntry['source'], text: string) {
    _logs = [
      ..._logs,
      { id: String(_nextId++), timestamp: new Date(), source, text },
    ];
    if (_logs.length > 500) _logs = _logs.slice(-500);
    notify();
  },

  getAll(): LogEntry[] {
    return _logs;
  },

  clear() {
    _logs = [];
    _nextId = 0;
    notify();
  },

  subscribe(listener: Listener): () => void {
    _listeners = [..._listeners, listener];
    return () => {
      _listeners = _listeners.filter((fn) => fn !== listener);
    };
  },
};

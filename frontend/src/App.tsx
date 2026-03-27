import { useState, useRef, useEffect } from 'react';

// !! Replace this with your actual API Gateway URL from Step 4 !!
const API_URL = 'https://x6xk0yj38j.execute-api.us-east-1.amazonaws.com/prod/chat';

type Message = {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
};

type Severity = 'HIGH' | 'MEDIUM' | 'LOW' | null;

// Pulls the confidence level out of Claude's response
function parseSeverity(text: string): Severity {
  if (text.includes('[HIGH]')) return 'HIGH';
  if (text.includes('[MEDIUM]')) return 'MEDIUM';
  if (text.includes('[LOW]')) return 'LOW';
  return null;
}

// Extracts IOCs from a block of text using regex patterns
function extractIOCs(text: string): string[] {
  const patterns = [
    /\b(?:\d{1,3}\.){3}\d{1,3}\b/g,              // IP addresses
    /CVE-\d{4}-\d{4,}/g,                           // CVE IDs
    /T\d{4}(?:\.\d{3})?/g,                         // MITRE ATT&CK IDs
    /\b[a-fA-F0-9]{32}\b|\b[a-fA-F0-9]{40}\b|\b[a-fA-F0-9]{64}\b/g, // Hashes
    /\b(?:[a-z0-9-]+\.)+(?:com|net|org|io|gov)\b/g, // Domains
  ];
  const iocs: string[] = [];
  patterns.forEach(p => {
    const matches = text.match(p);
    if (matches) iocs.push(...matches);
  });
  return Array.from(new Set(iocs)); // deduplicate
}

function SeverityBadge({ severity }: { severity: Severity }) {
  if (!severity) return null;
  const colours: Record<string, string> = {
    HIGH:   { bg: '#3b1a1a', border: '#ef4444', text: '#fca5a5' },
    MEDIUM: { bg: '#3b2a0a', border: '#f59e0b', text: '#fcd34d' },
    LOW:    { bg: '#0a2a1a', border: '#22c55e', text: '#86efac' },
  }[severity] ?? {};
  return (
    <span style={{
      backgroundColor: colours.bg,
      border: `1px solid ${colours.border}`,
      color: colours.text,
      borderRadius: '4px',
      padding: '2px 8px',
      fontSize: '11px',
      fontWeight: 600,
      letterSpacing: '0.5px',
      marginRight: '8px',
    }}>
      {severity}
    </span>
  );
}

function MessageBubble({ msg, onCopyIOCs }: {
  msg: Message;
  onCopyIOCs: (text: string) => void;
}) {
  const isUser = msg.role === 'user';
  const severity = isUser ? null : parseSeverity(msg.content);

  return (
    <div style={{
      alignSelf: isUser ? 'flex-end' : 'flex-start',
      maxWidth: '80%',
      display: 'flex',
      flexDirection: 'column',
      gap: '4px',
    }}>
      {/* Label row */}
      <div style={{
        fontSize: '11px',
        color: '#6b7280',
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
        paddingLeft: '4px',
      }}>
        {isUser ? 'You' : '🤖 SOC Assistant'} · {msg.timestamp}
      </div>

      {/* Bubble */}
      <div style={{
        backgroundColor: isUser ? '#1e3a5f' : '#1a1d27',
        border: `1px solid ${isUser ? '#2563eb' : '#2a2d3a'}`,
        borderRadius: isUser ? '12px 12px 2px 12px' : '12px 12px 12px 2px',
        padding: '12px 16px',
      }}>
        {/* Severity badge for assistant messages */}
        {severity && (
          <div style={{ marginBottom: '8px' }}>
            <SeverityBadge severity={severity} />
          </div>
        )}

        {/* Message text — preserve newlines */}
        <div style={{
          fontSize: '14px',
          lineHeight: 1.7,
          color: '#e0e0e0',
          whiteSpace: 'pre-wrap',
        }}>
          {msg.content}
        </div>

        {/* Copy IOCs button — only on assistant messages */}
        {!isUser && (
          <button
            onClick={() => onCopyIOCs(msg.content)}
            style={{
              marginTop: '10px',
              backgroundColor: 'transparent',
              border: '1px solid #2563eb',
              color: '#60a5fa',
              borderRadius: '6px',
              padding: '4px 12px',
              fontSize: '11px',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            Copy IOCs
          </button>
        )}
      </div>
    </div>
  );
}

// Quick-fire prompt chips along the bottom
const QUICK_PROMPTS = [
  'What are APT29 TTPs?',
  'Explain Log4Shell CVE-2021-44228',
  'What is a Golden Ticket attack?',
  'How does ransomware establish persistence?',
  'What IOCs indicate Cobalt Strike?',
  'Explain LSASS credential dumping',
];

export default function App() {
  const [messages, setMessages] = useState<Message[]>([{
    role: 'assistant',
    content: '🛡️ SOC Analyst Assistant online.\n\nAsk me about threat actors, CVEs, TTPs, MITRE ATT&CK techniques, or IOCs. I will always state my confidence level and structure answers clearly.',
    timestamp: new Date().toLocaleTimeString(),
  }]);
  const [input, setInput]       = useState('');
  const [loading, setLoading]   = useState(false);
  const [toast, setToast]       = useState('');
  const [sessionId]             = useState(() => `session-${Date.now()}`);
  const bottomRef               = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-dismiss toast after 3 seconds
  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(''), 3000);
      return () => clearTimeout(t);
    }
  }, [toast]);

  const sendMessage = async (text?: string) => {
    const messageText = (text ?? input).trim();
    if (!messageText || loading) return;

    const userMsg: Message = {
      role: 'user',
      content: messageText,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message: messageText }),
      });

      const data = await res.json();

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.reply ?? 'No response received.',
        timestamp: new Date().toLocaleTimeString(),
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '⚠️ Could not reach the backend. Check your API URL in App.tsx.',
        timestamp: new Date().toLocaleTimeString(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  const copyIOCs = (text: string) => {
    const iocs = extractIOCs(text);
    if (iocs.length === 0) {
      setToast('No IOCs detected in this message');
      return;
    }
    navigator.clipboard.writeText(iocs.join('\n'));
    setToast(`✓ Copied ${iocs.length} IOC${iocs.length > 1 ? 's' : ''} to clipboard`);
  };

  const clearSession = () => {
    setMessages([{
      role: 'assistant',
      content: '🛡️ Session cleared. Starting fresh.',
      timestamp: new Date().toLocaleTimeString(),
    }]);
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      backgroundColor: '#0f1117',
      color: '#e0e0e0',
      fontFamily: 'system-ui, -apple-system, sans-serif',
    }}>

      {/* Header */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '14px 20px',
        backgroundColor: '#1a1d27',
        borderBottom: '1px solid #2a2d3a',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '26px' }}>🛡️</span>
          <div>
            <div style={{ fontSize: '17px', fontWeight: 600, color: '#ffffff' }}>
              Threat Intelligence Assistant
            </div>
            <div style={{ fontSize: '12px', color: '#6b7280' }}>
              Amazon Bedrock · Claude 3.5 Sonnet · Session: {sessionId.slice(-6)}
            </div>
          </div>
        </div>
        <button
          onClick={clearSession}
          style={{
            backgroundColor: 'transparent',
            border: '1px solid #2a2d3a',
            color: '#6b7280',
            borderRadius: '6px',
            padding: '6px 14px',
            fontSize: '12px',
            cursor: 'pointer',
          }}
        >
          Clear session
        </button>
      </header>

      {/* Message list */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
      }}>
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} onCopyIOCs={copyIOCs} />
        ))}

        {/* Typing indicator */}
        {loading && (
          <div style={{
            alignSelf: 'flex-start',
            backgroundColor: '#1a1d27',
            border: '1px solid #2a2d3a',
            borderRadius: '12px 12px 12px 2px',
            padding: '12px 16px',
            fontSize: '14px',
            color: '#6b7280',
          }}>
            Analysing threat intelligence...
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick prompt chips */}
      <div style={{
        display: 'flex',
        gap: '8px',
        padding: '10px 20px',
        flexWrap: 'wrap',
        backgroundColor: '#1a1d27',
        borderTop: '1px solid #2a2d3a',
      }}>
        {QUICK_PROMPTS.map(q => (
          <button
            key={q}
            onClick={() => sendMessage(q)}
            disabled={loading}
            style={{
              backgroundColor: '#0f1117',
              border: '1px solid #2a2d3a',
              color: '#93c5fd',
              borderRadius: '16px',
              padding: '5px 12px',
              fontSize: '12px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.5 : 1,
            }}
          >
            {q}
          </button>
        ))}
      </div>

      {/* Input area */}
      <div style={{
        display: 'flex',
        gap: '8px',
        padding: '14px 20px',
        backgroundColor: '#1a1d27',
        borderTop: '1px solid #2a2d3a',
        flexShrink: 0,
      }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
          placeholder="Ask about CVEs, threat actors, TTPs, IOCs..."
          disabled={loading}
          style={{
            flex: 1,
            backgroundColor: '#0f1117',
            border: '1px solid #2a2d3a',
            borderRadius: '8px',
            padding: '10px 14px',
            color: '#e0e0e0',
            fontSize: '14px',
            outline: 'none',
          }}
        />
        <button
          onClick={() => sendMessage()}
          disabled={loading}
          style={{
            backgroundColor: loading ? '#1e3a5f' : '#2563eb',
            border: 'none',
            borderRadius: '8px',
            padding: '10px 22px',
            color: 'white',
            fontWeight: 600,
            fontSize: '14px',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {loading ? '...' : 'Send'}
        </button>
      </div>

      {/* Toast notification */}
      {toast && (
        <div style={{
          position: 'fixed',
          bottom: '90px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: '#1e3a5f',
          border: '1px solid #2563eb',
          color: '#93c5fd',
          borderRadius: '8px',
          padding: '8px 20px',
          fontSize: '13px',
          fontWeight: 500,
          zIndex: 100,
        }}>
          {toast}
        </div>
      )}
    </div>
  );
}
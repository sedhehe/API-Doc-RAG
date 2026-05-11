'use client';

import { useEffect, useRef, useState } from 'react';

const DEFAULT_WS_URL = 'ws://localhost:8000/ws/rag';
const WELCOME_MESSAGE = {
  role: 'assistant',
  content: 'Welcome to AI search! Feel free to ask anything. How can I help you?'
};

function makeWebSocketUrl() {
  return process.env.NEXT_PUBLIC_RAG_WS_URL || DEFAULT_WS_URL;
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [history, setHistory] = useState([]);
  const [sources, setSources] = useState([]);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, [open]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, open, busy]);

  function startNewConversation() {
    setMessages([WELCOME_MESSAGE]);
    setHistory([]);
    setInput('');
    setError('');
    setBusy(false);
  }

  async function sendMessage(event) {
    event.preventDefault();

    const query = input.trim();
    if (!query || busy) {
      return;
    }

    const nextMessages = [...messages, { role: 'user', content: query }];
    const nextHistory = [...history];
    setMessages(nextMessages);
    setInput('');
    setBusy(true);
    setError('');

    try {
      await new Promise((resolve, reject) => {
        const socket = new WebSocket(makeWebSocketUrl());

        socket.onopen = () => {
          socket.send(JSON.stringify({ query, history: nextHistory }));
        };

            socket.onmessage = (messageEvent) => {
          try {
            const payload = JSON.parse(messageEvent.data);

            if (payload.type === 'answer') {
                  setMessages((current) => [...current, { role: 'assistant', content: payload.answer }]);
                  setHistory(Array.isArray(payload.history) ? payload.history : []);
                  setSources(Array.isArray(payload.sources) ? payload.sources : []);
              socket.close();
              resolve();
              return;
            }

            if (payload.type === 'error') {
              setError(payload.message || 'The assistant could not answer that request.');
              socket.close();
              reject(new Error(payload.message || 'WebSocket error'));
            }
          } catch (parseError) {
            setError('Received an unexpected response from the assistant.');
            socket.close();
            reject(parseError);
          }
        };

        socket.onerror = () => {
          setError('Unable to reach the assistant backend.');
          reject(new Error('WebSocket connection failed'));
        };
      });
    } catch (sendError) {
      if (!error) {
        setError(sendError instanceof Error ? sendError.message : 'Something went wrong.');
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button type="button" className="ask-ai-fab" onClick={() => setOpen(true)}>
        Ask AI
      </button>

      {open ? (
        <div className="chat-overlay" role="presentation" onClick={() => setOpen(false)}>
          <section className="chat-modal" role="dialog" aria-modal="true" aria-label="AI assistant" onClick={(event) => event.stopPropagation()}>
            <header className="chat-header">
              <div>
                <p className="chat-eyebrow">Assistant</p>
                <h3>Ask the RAG model</h3>
              </div>
              <button type="button" className="chat-ghost-button" onClick={startNewConversation}>
                New conversation
              </button>
            </header>

            <div className="chat-body" ref={scrollRef}>
              {messages.map((message, index) => (
                <div key={`${message.role}-${index}`} className={`chat-message chat-message-${message.role}`}>
                  <div className="chat-bubble">{message.content}</div>
                </div>
              ))}

              {sources && sources.length > 0 ? (
                <div className="chat-sources" style={{ marginTop: 12 }}>
                  <div style={{ fontWeight: 800, marginBottom: 8 }}>Sources</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {sources.map((s, i) => {
                      const src = s.source_url || s.sourceUrl || s.metadata?.source_url || s.metadata?.sourceUrl || '';
                      const section = s.section || s.metadata?.section || '';
                      const parent = s.parent_section || s.metadata?.parent_section || '';

                      function onClickSource(e) {
                        e.preventDefault();
                        if (!src) {
                          return;
                        }

                        // close modal first so navigation is visible
                        setOpen(false);

                        try {
                          // Map internal doc links like '/docs/v2/api_reference#slug' to the root page
                          if (src.startsWith('/docs/')) {
                            const fragIndex = src.indexOf('#');
                            const frag = fragIndex >= 0 ? src.slice(fragIndex) : '';
                            window.location.href = '/' + (frag || '');
                            return;
                          }

                          const url = new URL(src, window.location.origin);
                          const isSamePath = url.pathname === window.location.pathname || url.pathname === '';

                          if (isSamePath && url.hash) {
                            // navigate to fragment on same page
                            window.location.hash = url.hash;
                          } else if (isSamePath && src.startsWith('#')) {
                            window.location.hash = src;
                          } else {
                            // navigate to the target path + fragment
                            window.location.href = url.pathname + (url.hash || '');
                          }
                        } catch (err) {
                          // fallback: if src contains a '#', use fragment
                          const idx = src.indexOf('#');
                          if (idx >= 0) {
                            const frag = src.slice(idx);
                            window.location.hash = frag;
                          } else {
                            window.open(src, '_blank');
                          }
                        }
                      }

                      return (
                        <a key={`source-${i}`} href={src || '#'} onClick={onClickSource} className="chat-source-link">
                          <div style={{ fontSize: '0.95rem', fontWeight: 700 }}>{section || src}</div>
                          <div style={{ fontSize: '0.85rem', color: '#617087' }}>{parent || src}</div>
                        </a>
                      );
                    })}
                  </div>
                </div>
              ) : null}

              {busy ? <div className="chat-status">Thinking through the docs...</div> : null}
            </div>

            {error ? <div className="chat-error">{error}</div> : null}

            <form className="chat-form" onSubmit={sendMessage}>
              <input
                type="text"
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask a question about the API docs..."
                aria-label="Ask a question"
              />
              <button type="submit" disabled={busy || !input.trim()}>
                Send
              </button>
            </form>
          </section>
        </div>
      ) : null}
    </>
  );
}

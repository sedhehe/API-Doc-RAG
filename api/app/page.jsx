import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import ChatWidget from '../components/chat-widget';
import { extractSections, loadReferenceDoc, renderableText, slugify } from '../lib/docs';

function MarkdownHeading(level, className) {
  return function Heading({ children, ...props }) {
    const text = renderableText(children);
    const id = slugify(text);
    const Tag = level;

    return (
      <Tag id={id} className={className} {...props}>
        {children}
      </Tag>
    );
  };
}

const markdownComponents = {
  h2: MarkdownHeading('h2', 'doc-h2'),
  h3: MarkdownHeading('h3', 'doc-h3'),
  h4: MarkdownHeading('h4', 'doc-h4'),
  p: ({ children }) => <p className="doc-paragraph">{children}</p>,
  ul: ({ children }) => <ul className="doc-list">{children}</ul>,
  ol: ({ children }) => <ol className="doc-list doc-list-ordered">{children}</ol>,
  li: ({ children }) => <li className="doc-list-item">{children}</li>,
  blockquote: ({ children }) => <blockquote className="doc-quote">{children}</blockquote>,
  table: ({ children }) => (
    <div className="doc-table-shell">
      <table className="doc-table">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead>{children}</thead>,
  tbody: ({ children }) => <tbody>{children}</tbody>,
  tr: ({ children }) => <tr>{children}</tr>,
  th: ({ children }) => <th>{children}</th>,
  td: ({ children }) => <td>{children}</td>,
  code: ({ inline, children }) => {
    if (inline) {
      return <code className="doc-inline-code">{children}</code>;
    }

    return <code>{children}</code>;
  },
  pre: ({ children }) => <pre className="doc-code-block">{children}</pre>,
  a: ({ children, href }) => (
    <a className="doc-link" href={href} target={href?.startsWith('http') ? '_blank' : undefined} rel="noreferrer">
      {children}
    </a>
  ),
};

export default async function Page() {
  const doc = await loadReferenceDoc();
  const sections = extractSections(doc.body);

  return (
    <div className="docs-app">
      <header className="topbar">
        <div>
          <p className="eyebrow">sedhehe</p>
          <h1>{doc.title}</h1>
          <p className="topbar-copy">{doc.intro}</p>
        </div>

        <div className="topbar-chip-row">
          <span className="topbar-chip">OpenAPI ready</span>
          <span className="topbar-chip">WebSocket assistant</span>
          <span className="topbar-chip">RAG-backed answers</span>
        </div>
      </header>

      <div className="docs-grid">
        <aside className="left-rail">
          <div className="panel panel-soft">
            <p className="panel-label">API reference</p>
            <nav className="section-nav">
              {sections.map((section) => (
                <a key={section.id} href={`#${section.id}`} className="section-nav-link">
                  <span>{section.title}</span>
                  <span className="section-nav-marker" />
                </a>
              ))}
            </nav>
          </div>
        </aside>

        <main className="content-column">
          <section className="hero-card">
            <div className="hero-kicker">Interactive reference</div>
            <h2>Ask questions without leaving the docs.</h2>
            <p>
              The page below is rendered directly from <code>docs/v2/api-reference.md</code> and the chat button in the
              corner connects to the FastAPI WebSocket RAG backend.
            </p>
          </section>

          <article className="doc-card">
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
              {doc.body}
            </ReactMarkdown>
          </article>
        </main>

        <aside className="right-rail">
          <div className="panel">
            <p className="panel-label">Download OpenAPI description</p>
            <div className="download-list">
              <a className="download-item" href="/api/download?file=api-reference.md">
                <span className="download-name">api-reference.md</span>
                <span className="download-meta">download markdown</span>
              </a>
              <a className="download-item" href="/api/download?file=api-reference.md">
                <span className="download-name">docs/v2/api-reference.md</span>
                <span className="download-meta">download source file</span>
              </a>
            </div>
          </div>

          <div className="panel">
            <p className="panel-label">Languages</p>
            <div className="language-grid">
              {['Python', 'JavaScript'].map((language) => (
                <span key={language} className="language-pill">
                  {language}
                </span>
              ))}
            </div>
          </div>

          <div className="panel">
            <p className="panel-label">Servers</p>
            <div className="server-item">
              <div>
                <div className="server-name">Backend</div>
                <div className="server-url">http://localhost:8000</div>
              </div>
              <div className="server-note">FastAPI</div>
            </div>
            <div className="server-item">
              <div>
                <div className="server-name">WebSocket</div>
                <div className="server-url">ws://localhost:8000/ws/rag</div>
              </div>
              <div className="server-note">Chat</div>
            </div>
          </div>

        </aside>
      </div>

      <ChatWidget />
    </div>
  );
}

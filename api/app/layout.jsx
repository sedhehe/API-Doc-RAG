import './globals.css';

export const metadata = {
  title: 'NexAPI Reference',
  description: 'Interactive docs experience with embedded RAG assistant',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

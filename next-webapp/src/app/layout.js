import './globals.css'

export const metadata = {
  title: 'Nyaya Mitra — AI Legal Guide for Indian Law',
  description: 'Free AI-powered legal assistant for Indian law. Ask about BNS, BNSS, BSA and Constitution. Bring Your Own Gemini API Key.',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>
        {/* Mesh Gradient Background */}
        <div className="mesh-bg">
          <div className="mesh-blob blob-1"></div>
          <div className="mesh-blob blob-2"></div>
          <div className="mesh-blob blob-3"></div>
        </div>
        {children}
      </body>
    </html>
  )
}

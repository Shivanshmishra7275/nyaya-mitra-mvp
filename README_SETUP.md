# Nyaya Mitra - AI Legal Helper

A powerful React + TypeScript + Vite application providing AI-powered legal assistance with document analysis and emergency support features. Built with Google's Generative AI (Gemini).

## ✨ Features

- **Legal Query Assistant**: Ask questions about Indian laws and get AI-powered responses
- **Document Analysis**: Upload legal documents for intelligent analysis
- **Emergency Panic Mode**: Voice-based emergency alert system with immediate legal guidance
- **Citation Grounding**: Automatic sourcing and citation of relevant legal references
- **Responsive UI**: Beautiful dark-themed interface with Tailwind CSS
- **Real-time Chat**: Multi-turn conversation history with context awareness

## 🔧 Prerequisites

- **Node.js** (v18 or higher)
- **npm** (v9 or higher)
- **Google Gemini API Key** (Get from [Google AI Studio](https://aistudio.google.com))

## 📦 Installation

1. Clone the repository:
   ```bash
   cd Nyaya-Mitra---A-legal-Helper-
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up your API key:
   - Open `.env` file in the root directory
   - Replace `your_gemini_api_key_here` with your actual Gemini API key:
   ```env
   VITE_GEMINI_API_KEY=your_actual_api_key_here
   ```

## 🚀 Running the App

Start the development server:
```bash
npm run dev
```

The app will be available at: **http://localhost:3001/**

### Other Commands

- **Build for production**: `npm run build`
- **Preview production build**: `npm run preview`

## 🎯 How to Use

### Legal Query
1. Type your legal question in the input field
2. Press Enter or click the Send button
3. Get AI-powered legal insights with relevant citations

### Document Analysis
1. Click the Camera icon
2. Select a legal document image/PDF
3. Ask specific questions about the document
4. Get detailed legal analysis

### Emergency Mode
1. Click the **"Panic"** button (red button in header)
2. Speak your emergency situation
3. Get immediate legal guidance and emergency protocols
4. The system will suggest relevant emergency contacts (e.g., 112 in India)

## 📁 Project Structure

```
├── index.tsx              # Main React component
├── index.html             # HTML entry point
├── package.json           # Project dependencies
├── tsconfig.json          # TypeScript configuration
├── vite.config.ts         # Vite configuration
├── .env                   # Environment variables (API key)
├── vite-env.d.ts          # Vite type definitions
├── google-generative-ai.d.ts  # Google AI SDK types
└── README.md              # This file
```

## 🔐 Security

- **Never commit `.env` file** - Keep your API key private
- Always use environment variables for sensitive data
- The app includes a disclaimer about professional legal advice

## 🛠️ Tech Stack

- **React 19.2** - UI Framework
- **TypeScript 5.8** - Type safety
- **Vite 6.2** - Build tool & dev server
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Google Generative AI SDK** - AI capabilities

## ⚠️ Disclaimer

**Important**: This application provides AI-generated legal assistance. It is **NOT a replacement for professional legal advice**. Always consult with a certified advocate for critical legal matters.

## 🐛 Troubleshooting

### API Key Errors
- Ensure `VITE_GEMINI_API_KEY` is correctly set in `.env`
- Verify your API key is valid and has Generative AI access

### Port 3001 Already in Use
- Vite will automatically try the next available port (3002, 3003, etc.)
- Or manually change the port in `vite.config.ts`

### Microphone Access Denied
- Grant microphone permissions in your browser settings
- Required for Emergency Panic Mode

## 📝 License

This project is provided as-is for educational and legal assistance purposes.

---

Made with ❤️ for legal accessibility in India

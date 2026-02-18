# 🧠 Mental Coach Chat Frontend

A slick, modern React chat interface for talking to your AI mental coach! Built with Next.js and Material-UI, styled with the iconic Google color palette. 🎨

## ✨ Features

- 💬 **Real-time chat** with your AI mental coach
- 🎯 **Clean, intuitive UI** following Google Material Design
- 📱 **Responsive design** that looks great on any device
- ⚡ **Fast & snappy** with Next.js under the hood
- 🌈 **Google color palette** for that familiar, trustworthy feel

## 🚀 Getting Started

### Prerequisites

Make sure you've got Node.js 18+ installed. Check with:

```bash
node --version
```

### Installation

1. Navigate to the UI directory:

```bash
cd ui
```

2. Install dependencies:

```bash
npm install
```

### Running Locally

1. **Start the backend first!** (in a separate terminal from the project root):

```bash
uv run uvicorn api.index:app --reload
```

2. **Then fire up the frontend**:

```bash
cd ui
npm run dev
```

3. **Open your browser** and head to [http://localhost:3000](http://localhost:3000) 🎉

### Environment Variables (Optional)

If your backend API is running on a different URL, create a `.env.local` file in the `/ui` directory:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🏗️ Project Structure

```
ui/
├── components/          # Reusable React components
│   └── ChatMessage/     # Chat bubble component
├── pages/               # Next.js pages (routes)
│   ├── _app.tsx         # App wrapper with theme
│   ├── _document.tsx    # Custom document with fonts
│   └── index.tsx        # Main chat page
├── services/            # API communication layer
│   └── chatService.ts   # Chat API calls
├── styles/              # Global styles
├── theme/               # Material-UI theme config
├── colors.css           # CSS color variables (Google palette)
└── package.json
```

## 🎨 Design System

We're rocking the **Official Google Color Palette**:

| Color | Hex | Usage |
|-------|-----|-------|
| 🔵 Google Blue | `#4285F4` | Primary actions, links |
| 🔴 Google Red | `#EA4335` | Errors, alerts |
| 🟡 Google Yellow | `#FBBC05` | Warnings |
| 🟢 Google Green | `#34A853` | Success states |

## 🛠️ Tech Stack

- **Framework**: [Next.js 14](https://nextjs.org/)
- **UI Library**: [Material-UI v5](https://mui.com/)
- **Language**: TypeScript
- **Styling**: CSS (no inline styles, no CSS-in-JS - keeping it clean!)

## 📝 Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Build for production |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |

## 🐛 Troubleshooting

**Chat not working?**
- Make sure the backend is running on `http://localhost:8000`
- Check that your `OPENAI_API_KEY` is set in the backend

**Styles look off?**
- Clear your browser cache and reload
- Make sure `npm install` completed successfully

## 🚀 Deployment

This frontend is ready to deploy on [Vercel](https://vercel.com)! Just connect your repo and you're good to go.

---

Built with ❤️ and ☕ for the AI Engineer Challenge

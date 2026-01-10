# Janett (TypeScript + Ink Rewrite)

AI-powered interactive tutorial generator built with **TypeScript**, **React**, and **Ink** for a beautiful terminal experience.

## 🎨 Features

- ✨ Beautiful terminal UI with gradient branding
- 🤖 Multi-provider AI support (OpenAI, Anthropic) via Vercel AI SDK
- 📚 Structured chapter-based tutorials
- 🧭 Easy chapter navigation (next/prev/goto)
- 🚀 Generate more chapters on demand
- 💬 Interactive chat mode (coming soon)
- ⌨️ Keyboard shortcuts
- 🎨 Syntax-highlighted code blocks
- 💾 Persistent configuration

## 🚀 Quick Start

### Install Dependencies

```bash
cd ink-app
npm install
```

### Set API Key

```bash
export OPENAI_API_KEY="your-key-here"
# or
export ANTHROPIC_API_KEY="your-key-here"
```

### Build

```bash
npm run build
```

### Run

```bash
node dist/cli.js
```

Or in development mode:

```bash
npm run dev
```

## 📖 Usage

1. **Start Janett**

   ```bash
   janett
   ```

2. **Enter a topic** (e.g., "Python basics", "Photography for beginners")

3. **Navigate chapters**
   - `/next` - Next chapter
   - `/prev` - Previous chapter
   - `/chapters` - View all chapters
   - `/goto 3` - Jump to chapter 3
   - `/more` - Generate more chapters
   - `/quit` - Exit

## 🏗️ Architecture

```
ink-app/
├── source/
│   ├── types.ts              # TypeScript types
│   ├── config.ts             # Configuration management
│   ├── ai.ts                 # AI service (Vercel AI SDK)
│   ├── app.tsx               # Main React component
│   ├── cli.tsx               # CLI entry point
│   └── components/
│       ├── Header.tsx        # Header with branding
│       ├── Welcome.tsx       # Welcome screen
│       ├── ChapterView.tsx   # Chapter display
│       ├── ChapterList.tsx   # Chapter navigation
│       ├── Loading.tsx       # Loading spinner
│       └── Input.tsx         # Input component
├── package.json
└── tsconfig.json
```

## 🎯 Tech Stack

- **Runtime**: Node.js 18+
- **Language**: TypeScript
- **UI Framework**: [Ink](https://github.com/vadimdemedes/ink) (React for CLIs)
- **AI SDK**: [Vercel AI SDK](https://sdk.vercel.ai/)
- **Providers**: OpenAI, Anthropic
- **CLI**: meow
- **Config**: conf
- **Styling**: chalk, ink-gradient, ink-big-text

## 🎨 UI Components

- **ink-gradient** - Gradient text effects
- **ink-big-text** - Large ASCII art text
- **ink-text-input** - Text input fields
- **ink-select-input** - Selection menus
- **ink-spinner** - Loading animations

## 🔧 Configuration

Config stored in `~/.janett/config.json`:

```json
{
	"openaiApiKey": "sk-...",
	"anthropicApiKey": "sk-ant-...",
	"defaultProvider": "openai",
	"defaultModel": "gpt-4o-mini"
}
```

## 📝 Commands

| Command     | Description            |
| ----------- | ---------------------- |
| `/next`     | Go to next chapter     |
| `/prev`     | Go to previous chapter |
| `/chapters` | View all chapters      |
| `/goto [N]` | Jump to chapter N      |
| `/more`     | Generate more chapters |
| `/chat`     | Switch to chat mode    |
| `/quit`     | Exit Janett            |

## 🚧 Status

**Current Progress**:

- ✅ Project scaffold with Ink 5
- ✅ TypeScript types defined
- ✅ AI service with Vercel AI SDK
- ✅ Configuration management
- ✅ Core UI components (Header, Welcome, ChapterView, etc.)
- ✅ Main app logic with command routing
- ✅ Navigation system
- ✅ Tutorial generation
- ✅ Chapter continuation

**Todo**:

- ⏳ Fix remaining TypeScript strict mode errors (3 minor)
- ⏳ Implement chat mode UI
- ⏳ Add settings screen
- ⏳ Add keyboard shortcuts help
- ⏳ Improve markdown rendering
- ⏳ Add Ollama support

## 🎨 UX Inspiration

Inspired by **Claude Code** with:

- Minimal, clean design
- Gradient branding
- Clear typography
- Smooth interactions
- Helpful prompts

## 📦 Publishing

To publish to npm:

```bash
npm run build
npm publish
```

Then install globally:

```bash
npm install -g janett
janett
```

## 🤝 Contributing

This is a rewrite of the original Python version using modern web technologies for the terminal. Contributions welcome!

## 📄 License

MIT

---

**Built with ❤️ using TypeScript, React, and Ink**

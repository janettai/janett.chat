# Janett - Product Development Document

## Overview

Janett is an AI-powered interactive tutorial generator that creates structured, chapter-based learning experiences on any topic. Currently available as a CLI application, with plans for a web-based version.

---

## Current Features (CLI v0.2.0)

### Core Features

#### 1. Tutorial Generation
- **Topic Input**: User enters any topic (e.g., "Python basics", "Photography for beginners")
- **Structured Output**: AI generates 4-6 chapters with:
  - Tutorial title and description
  - Chapter titles and summaries
  - Full markdown content with examples
- **Format**: Uses structured text markers (`===TUTORIAL===`, `===CHAPTER N===`) for reliable parsing

#### 2. Chapter Navigation
- **Sequential**: `/next`, `/prev` for linear progression
- **Direct Jump**: `/goto <n>` to jump to specific chapter
- **Chapter List**: `/chapters` shows all chapters with current position highlighted
- **Progress Indicator**: Header shows "Ch 2/5" style progress

#### 3. Learn More (Continuation)
- **Generate More**: `/more [n]` adds 1-5 additional chapters
- **Context Aware**: New chapters build on existing content
- **Seamless Integration**: New chapters appended to tutorial, user jumps to first new chapter

#### 4. Chat Mode
- **In-Tutorial Chat**: `/chat` to ask questions without leaving tutorial
- **Same Provider**: Uses same AI model/provider as tutorial
- **Return**: `/back` returns to tutorial view

### Provider System

#### 5. Multi-Provider Support
- **Ollama (Default)**: Local, free, private AI inference
- **OpenAI**: Cloud-based with API key
- **Switch Anytime**: `/provider` command to switch

#### 6. Model Selection
- **Auto-Detection**: Ollama models detected automatically via API
- **Model List**: `/models` shows available models for current provider
- **Easy Switch**: Select model by name

#### 7. API Key Management
- **Secure Storage**: Keys saved to `~/.janett/config.json`
- **Environment Support**: Also reads `OPENAI_API_KEY` env var
- **Masked Display**: Shows `sk-proj-...xxxx` format

### User Experience

#### 8. Rich Terminal UI
- **Styled Header**: App name, model, provider, chapter progress
- **Markdown Rendering**: Code blocks, lists, bold, etc.
- **Colored Output**: Theme with primary, success, error, muted colors
- **Panels**: Chapter content in bordered panels

#### 9. Command History
- **Up/Down Arrows**: Navigate previous commands
- **Persistent**: History saved to `~/.janett/history`
- **1000 Entry Limit**: Reasonable history size

#### 10. Welcome Experience
- **Tutorial Mode**: Shows welcome message with example topics
- **Help Available**: `/help` shows all commands
- **Guided**: Clear prompts for what to do next

### Configuration

#### 11. Settings Persistence
- **Config Directory**: `~/.janett/`
- **Files**:
  - `config.json` - API keys, preferences
  - `history` - Command history

#### 12. Timeout Configuration
- **5 Minute Default**: `API_TIMEOUT = 300` seconds
- **Configurable**: Can adjust in config.py

---

## Web Application Plan

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  Next.js / React + TailwindCSS + shadcn/ui                  │
├─────────────────────────────────────────────────────────────┤
│                         API                                  │
│  Next.js API Routes / FastAPI                               │
├─────────────────────────────────────────────────────────────┤
│                       Backend                                │
│  Python (reuse janett core) / Node.js                       │
├─────────────────────────────────────────────────────────────┤
│                      Database                                │
│  PostgreSQL / SQLite (tutorials, users, progress)           │
├─────────────────────────────────────────────────────────────┤
│                    AI Providers                              │
│  Ollama (local) / OpenAI / Anthropic                        │
└─────────────────────────────────────────────────────────────┘
```

### Web Features Mapping

| CLI Feature | Web Equivalent |
|-------------|----------------|
| Topic input | Search/input bar with suggestions |
| Chapter navigation | Sidebar + prev/next buttons |
| Chapter content | Main content area with markdown |
| `/more` command | "Generate More" button |
| `/chat` mode | Slide-out chat panel |
| `/models` | Settings dropdown |
| `/provider` | Settings page |
| Command history | Recent tutorials list |
| Progress indicator | Progress bar + chapter dots |

### Web-Specific Features

#### Authentication & Accounts
- [ ] User registration/login
- [ ] OAuth (Google, GitHub)
- [ ] Guest mode (limited usage)

#### Tutorial Management
- [ ] Save tutorials to account
- [ ] Tutorial library/history
- [ ] Share tutorials (public links)
- [ ] Export to PDF/Markdown
- [ ] Bookmark chapters

#### Enhanced Learning
- [ ] Progress tracking per tutorial
- [ ] Mark chapters as complete
- [ ] Quizzes at end of chapters
- [ ] Code playground (for programming topics)
- [ ] Notes/annotations per chapter

#### Social Features
- [ ] Public tutorial gallery
- [ ] Upvote/favorite tutorials
- [ ] Comments on tutorials
- [ ] User profiles with tutorial history

#### AI Enhancements
- [ ] Multiple AI providers (OpenAI, Anthropic, Ollama)
- [ ] Custom system prompts
- [ ] Difficulty levels (beginner/intermediate/advanced)
- [ ] Language selection
- [ ] Voice narration (TTS)

#### UI/UX
- [ ] Dark/light mode
- [ ] Mobile responsive
- [ ] Keyboard shortcuts
- [ ] Reading time estimates
- [ ] Table of contents sidebar
- [ ] Search within tutorial

### Pages Structure

```
/                       # Landing page
/learn                  # Tutorial generator (main app)
/learn/[id]             # View saved tutorial
/learn/[id]/[chapter]   # Specific chapter
/library                # User's saved tutorials
/explore                # Public tutorial gallery
/settings               # User settings, API keys
/pricing                # Plans (if monetized)
```

### API Endpoints

```
POST   /api/tutorials/generate     # Generate new tutorial
POST   /api/tutorials/[id]/more    # Generate more chapters
GET    /api/tutorials              # List user's tutorials
GET    /api/tutorials/[id]         # Get tutorial details
DELETE /api/tutorials/[id]         # Delete tutorial
POST   /api/chat                   # Chat within tutorial context
GET    /api/models                 # List available models
POST   /api/settings/apikey        # Save API key
```

### Data Models

```typescript
// Tutorial
{
  id: string
  userId: string
  title: string
  description: string
  topic: string
  provider: 'ollama' | 'openai' | 'anthropic'
  model: string
  chapters: Chapter[]
  createdAt: Date
  updatedAt: Date
  isPublic: boolean
}

// Chapter
{
  id: number
  title: string
  summary: string
  content: string  // Markdown
  isCompleted: boolean
}

// User
{
  id: string
  email: string
  name: string
  apiKeys: {
    openai?: string (encrypted)
    anthropic?: string (encrypted)
  }
  preferences: {
    defaultProvider: string
    defaultModel: string
    theme: 'light' | 'dark'
  }
}
```

### Tech Stack Recommendation

#### Option A: Full Next.js (Recommended for MVP)
- **Frontend**: Next.js 14+ App Router
- **Styling**: TailwindCSS + shadcn/ui
- **Database**: Vercel Postgres or PlanetScale
- **Auth**: NextAuth.js / Clerk
- **AI**: Vercel AI SDK
- **Deployment**: Vercel

#### Option B: Separate Frontend/Backend
- **Frontend**: React + Vite
- **Backend**: FastAPI (Python) - reuse Janett core
- **Database**: PostgreSQL
- **Auth**: Auth0 / Supabase Auth
- **Deployment**: Frontend on Vercel, Backend on Railway/Fly.io

### MVP Scope (v1.0)

#### Must Have
- [ ] Tutorial generation with chapters
- [ ] Chapter navigation (next/prev/goto)
- [ ] Markdown rendering
- [ ] Generate more chapters
- [ ] Save tutorials (local storage initially)
- [ ] Dark/light mode
- [ ] Mobile responsive

#### Should Have
- [ ] User accounts
- [ ] Tutorial library
- [ ] OpenAI integration
- [ ] Share tutorials

#### Nice to Have
- [ ] Ollama support (local)
- [ ] Chat mode
- [ ] Quizzes
- [ ] Export

### Development Phases

#### Phase 1: Core Tutorial Experience (2-3 weeks)
- Landing page
- Tutorial generation UI
- Chapter display with markdown
- Navigation (next/prev)
- Local storage for tutorials

#### Phase 2: User Accounts (1-2 weeks)
- Authentication
- Save tutorials to database
- Tutorial library page

#### Phase 3: Enhanced Features (2-3 weeks)
- Generate more chapters
- Chat mode
- Multiple AI providers
- Settings page

#### Phase 4: Social & Polish (2-3 weeks)
- Public tutorials
- Share functionality
- Mobile optimization
- Performance optimization

---

## File Structure (Web)

```
janett-web/
├── app/
│   ├── page.tsx                 # Landing
│   ├── learn/
│   │   ├── page.tsx             # Tutorial generator
│   │   └── [id]/
│   │       └── page.tsx         # Tutorial viewer
│   ├── library/
│   │   └── page.tsx             # Saved tutorials
│   ├── settings/
│   │   └── page.tsx             # Settings
│   └── api/
│       ├── tutorials/
│       │   └── route.ts
│       └── chat/
│           └── route.ts
├── components/
│   ├── tutorial/
│   │   ├── TutorialGenerator.tsx
│   │   ├── ChapterView.tsx
│   │   ├── ChapterList.tsx
│   │   └── NavigationButtons.tsx
│   ├── chat/
│   │   └── ChatPanel.tsx
│   └── ui/
│       └── (shadcn components)
├── lib/
│   ├── ai.ts                    # AI provider logic
│   ├── parser.ts                # Tutorial parsing
│   └── db.ts                    # Database
└── types/
    └── index.ts                 # TypeScript types
```

---

## Success Metrics

- **Engagement**: Tutorials generated per user
- **Retention**: Users returning within 7 days
- **Completion**: Chapters completed per tutorial
- **Growth**: New user signups
- **Satisfaction**: NPS score, feedback

---

## Monetization Options (Future)

1. **Freemium**: Free tier with limits, paid for unlimited
2. **API Credits**: Pay per tutorial generated
3. **Pro Features**: Advanced AI models, export, no ads
4. **Team Plans**: Shared libraries, collaboration

---

## References

- CLI Source: `src/janett/`
- Tutorial Parser: `src/janett/tutorial.py`
- UI Components: `src/janett/ui.py`
- Config: `src/janett/config.py`

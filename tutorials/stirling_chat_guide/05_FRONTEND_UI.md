# Part 5: Frontend & User Interface

## 🎯 Learning Objectives

By the end of this section, you will understand:
- React component structure
- State management with hooks
- API integration with Axios
- The chat widget UI/UX design
- Styling with TailwindCSS
- Docker containerization for frontend

---

## 5.1 Technology Stack

| Technology | Purpose | Version |
|------------|---------|---------|
| **React** | UI framework | 18.x |
| **Vite** | Build tool & dev server | 5.x |
| **TailwindCSS** | Utility-first CSS | 3.x |
| **Axios** | HTTP client | 1.x |
| **Lucide React** | Icon library | Latest |

---

## 5.2 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatWidget.jsx      # Main chat component (500+ lines)
│   │   └── FeedbackModal.jsx   # Rating modal
│   ├── App.jsx                 # Root component
│   ├── config.js               # API endpoints
│   ├── main.jsx                # Entry point
│   └── index.css               # Global styles + Tailwind
├── public/
│   └── index.html
├── Dockerfile                  # Container config
├── package.json
├── vite.config.js
└── tailwind.config.js
```

---

## 5.3 Configuration

### API Endpoints

**File:** `frontend/src/config.js`

```javascript
// API base URL - uses environment variable or defaults to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  CHAT: `${API_BASE_URL}/api/chat`,
  CONVERSATION: (sessionId) => `${API_BASE_URL}/api/conversation/${sessionId}`,
  END_CONVERSATION: (sessionId) => `${API_BASE_URL}/api/conversation/${sessionId}/end`,
  FEEDBACK: `${API_BASE_URL}/api/feedback`,
  HEALTH: `${API_BASE_URL}/health`,
};

export const CHAT_CONFIG = {
  MAX_MESSAGE_LENGTH: 2000,
  AUTO_SCROLL_DELAY: 100,
  TYPING_INDICATOR_DELAY: 500,
};
```

### Vite Configuration

**File:** `frontend/vite.config.js`

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',  // Allow external access
    port: 3000,
  },
})
```

---

## 5.4 The ChatWidget Component

**File:** `frontend/src/components/ChatWidget.jsx`

This is the main component (~540 lines). Let's break it down section by section.

### State Management

```javascript
export default function ChatWidget() {
  // UI State
  const [isOpen, setIsOpen] = useState(false)           // Chat window open/closed
  const [isMinimized, setIsMinimized] = useState(false) // Minimized state
  const [isFullscreen, setIsFullscreen] = useState(false) // Fullscreen mode
  
  // Chat State
  const [messages, setMessages] = useState([])          // Array of messages
  const [inputMessage, setInputMessage] = useState('')  // Current input
  const [isLoading, setIsLoading] = useState(false)     // Loading indicator
  const [sessionId, setSessionId] = useState(null)      // Session identifier
  
  // Feedback State
  const [showFeedback, setShowFeedback] = useState(false)
  const [conversationSummary, setConversationSummary] = useState(null)
  
  // Refs for DOM manipulation
  const messagesEndRef = useRef(null)       // Scroll to bottom
  const messagesContainerRef = useRef(null) // Messages container
  const lastMessageRef = useRef(null)       // Last message for scroll
  const inputRef = useRef(null)             // Input field for focus
```

### Message Structure

```javascript
// User message
{
  role: 'user',
  content: 'What are the fees for MSc AI?',
  timestamp: new Date()
}

// Assistant message
{
  role: 'assistant',
  content: 'MSc AI fees are £24,300/year...',
  sources: [
    { title: 'Source', url: 'https://stir.ac.uk/courses/msc-ai/' }
  ],
  timestamp: new Date()
}
```

---

## 5.5 Sending Messages

### The handleSendMessage Function

```javascript
const handleSendMessage = async () => {
  // 1. Validate input
  if (!inputMessage.trim() || isLoading) return

  const userMessage = inputMessage.trim()
  setInputMessage('')  // Clear input immediately

  // 2. Add user message to UI (optimistic update)
  setMessages(prev => [...prev, {
    role: 'user',
    content: userMessage,
    timestamp: new Date()
  }])
  
  // 3. Scroll to show user's message
  scrollToNewMessage(true)

  // 4. Show loading state
  setIsLoading(true)

  try {
    // 5. Send to backend
    const response = await axios.post(API_ENDPOINTS.CHAT, {
      message: userMessage,
      session_id: sessionId
    })

    const data = response.data

    // 6. Save session ID (first message creates session)
    if (!sessionId) {
      setSessionId(data.session_id)
    }

    // 7. Add bot response to UI
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: data.answer,
      sources: data.sources || [],
      timestamp: new Date()
    }])
    
    // 8. Scroll to show response
    setTimeout(() => scrollToNewMessage(false), 100)

  } catch (error) {
    // 9. Handle errors gracefully
    console.error('Chat error:', error)
    setMessages(prev => [...prev, {
      role: 'assistant',
      content: 'Sorry, I encountered an error. Please try again.',
      timestamp: new Date(),
      isError: true
    }])
  } finally {
    // 10. Reset loading and focus input
    setIsLoading(false)
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.focus()
      }
    }, 100)
  }
}
```

### Keyboard Handling

```javascript
const handleKeyPress = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()  // Prevent newline
    handleSendMessage()
  }
}
```

---

## 5.6 Smart Scrolling

The chat uses smart scrolling to provide the best UX:

```javascript
const scrollToNewMessage = (isUserMessage = false) => {
  setTimeout(() => {
    if (isUserMessage) {
      // User messages: scroll to bottom so they see their message
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    } else {
      // Bot messages: scroll to TOP of message so user can read from start
      if (lastMessageRef.current) {
        lastMessageRef.current.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'start' 
        })
      }
    }
  }, CHAT_CONFIG.AUTO_SCROLL_DELAY)
}
```

### Auto-Focus on Open

```javascript
useEffect(() => {
  if (isOpen && !isMinimized && inputRef.current) {
    inputRef.current.focus()
  }
}, [isOpen, isMinimized])
```

---

## 5.7 Message Rendering

### Markdown-like Formatting

```javascript
const renderInlineBold = (text) => {
  if (!text) return text;
  
  // Split on **bold** patterns
  const parts = text.split(/(\*\*.*?\*\*)/g);
  
  return parts.map((part, j) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      // Render as bold
      return <strong key={j} className="font-semibold">{part.slice(2, -2)}</strong>;
    }
    return part;
  });
};
```

### Full Message Rendering

```javascript
const renderMessageContent = (content) => {
  if (!content) return null;
  
  // Split into paragraphs
  const paragraphs = content.split('\n\n');
  
  return paragraphs.map((para, i) => {
    // Check for bullet points
    if (para.includes('\n- ') || para.startsWith('- ')) {
      const items = para.split('\n').filter(line => line.startsWith('- '));
      return (
        <ul key={i} className="list-disc list-inside space-y-1 my-2">
          {items.map((item, j) => (
            <li key={j} className="text-gray-700">
              {renderInlineBold(item.substring(2))}
            </li>
          ))}
        </ul>
      );
    }
    
    // Regular paragraph
    return (
      <p key={i} className="mb-2 last:mb-0">
        {renderInlineBold(para)}
      </p>
    );
  });
};
```

---

## 5.8 UI Components

### Floating Chat Button

```jsx
{/* Floating button when chat is closed */}
{!isOpen && (
  <button
    onClick={() => setIsOpen(true)}
    className="group relative bg-gradient-to-r from-green-600 to-green-700 
               text-white rounded-full p-4 shadow-2xl 
               hover:shadow-green-500/25 hover:scale-110 
               transition-all duration-300"
  >
    <MessageCircle className="w-7 h-7" />
    
    {/* Green online indicator */}
    <span className="absolute -top-2 -right-2 w-4 h-4 
                     bg-green-400 rounded-full border-2 border-white 
                     animate-pulse" />
  </button>
)}
```

### Chat Header

```jsx
<div className="bg-gradient-to-r from-green-600 to-green-700 
                text-white p-4 flex items-center justify-between">
  <div className="flex items-center gap-3">
    {messages.length > 0 && (
      <img 
        src="/stirling-logo.png" 
        alt="Stirling" 
        className="h-8 w-auto animate-fadeInLogo"
      />
    )}
    <div>
      <h3 className="font-semibold text-lg">Stirling Assistant</h3>
      <div className="flex items-center gap-2 text-green-100 text-sm">
        <span className="w-2 h-2 bg-green-300 rounded-full animate-pulse" />
        <span>Online</span>
      </div>
    </div>
  </div>
  
  {/* Control buttons */}
  <div className="flex items-center gap-2">
    <button onClick={() => setIsFullscreen(!isFullscreen)}>
      {isFullscreen ? <Minimize2 /> : <Maximize2 />}
    </button>
    <button onClick={handleEndChat}>
      <X />
    </button>
  </div>
</div>
```

### Welcome Screen

```jsx
{messages.length === 0 && (
  <div className="text-center py-8 animate-fadeIn">
    <div className="inline-flex items-center justify-center 
                    w-16 h-16 rounded-full 
                    bg-gradient-to-br from-green-100 to-green-200 
                    mb-4 shadow-lg">
      <GraduationCap className="w-8 h-8 text-green-600" />
    </div>
    
    <h4 className="text-lg font-semibold text-gray-800 mb-2">
      Welcome to Stirling!
    </h4>
    
    <p className="text-gray-600 text-sm max-w-xs mx-auto">
      I'm here to help you explore courses, understand requirements, 
      and guide your journey to the University of Stirling.
    </p>
    
    {/* Quick topic buttons */}
    <div className="mt-6 flex flex-wrap justify-center gap-2">
      {['Courses', 'Fees', 'Requirements', 'Campus Life'].map((topic) => (
        <button
          key={topic}
          onClick={() => setInputMessage(`Tell me about ${topic.toLowerCase()}`)}
          className="px-4 py-2 bg-white border border-gray-200 
                     rounded-full text-sm text-gray-700 
                     hover:border-green-500 hover:text-green-600 
                     hover:bg-green-50 transition-all shadow-sm"
        >
          {topic}
        </button>
      ))}
    </div>
  </div>
)}
```

### Message Bubbles

```jsx
{messages.map((message, index) => (
  <div
    key={index}
    ref={index === messages.length - 1 ? lastMessageRef : null}
    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
  >
    <div className={`max-w-[85%] rounded-2xl px-4 py-3 shadow-sm
      ${message.role === 'user'
        ? 'bg-gradient-to-r from-green-600 to-green-700 text-white rounded-br-md'
        : 'bg-white text-gray-800 border border-gray-100 rounded-bl-md'
      }
      ${message.isError ? 'bg-red-50 border-red-200 text-red-700' : ''}
    `}>
      {renderMessageContent(message.content)}
      
      {/* Sources */}
      {message.sources?.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-2">Sources:</p>
          {message.sources.map((source, i) => (
            <a
              key={i}
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-green-600 
                         hover:text-green-700 hover:underline"
            >
              <ExternalLink className="w-3 h-3" />
              {new URL(source.url).hostname}
            </a>
          ))}
        </div>
      )}
    </div>
  </div>
))}
```

### Input Area

```jsx
<div className="p-4 border-t border-gray-100 bg-white">
  <div className="flex items-end gap-2">
    <textarea
      ref={inputRef}
      value={inputMessage}
      onChange={(e) => setInputMessage(e.target.value)}
      onKeyPress={handleKeyPress}
      placeholder="Type your message..."
      disabled={isLoading}
      rows={1}
      className="flex-1 resize-none rounded-xl border border-gray-200 
                 px-4 py-3 text-sm focus:outline-none focus:ring-2 
                 focus:ring-green-500 focus:border-transparent
                 disabled:bg-gray-50 disabled:text-gray-400"
    />
    
    <button
      onClick={handleSendMessage}
      disabled={!inputMessage.trim() || isLoading}
      className="bg-gradient-to-r from-green-600 to-green-700 
                 text-white rounded-xl p-3 
                 hover:shadow-lg hover:scale-105 
                 disabled:opacity-50 disabled:cursor-not-allowed 
                 transition-all duration-200"
    >
      <Send className="w-5 h-5" />
    </button>
  </div>
</div>
```

---

## 5.9 Loading Indicator

```jsx
{isLoading && (
  <div className="flex justify-start">
    <div className="bg-white rounded-2xl rounded-bl-md px-4 py-3 
                    shadow-sm border border-gray-100">
      <div className="flex items-center gap-2">
        <div className="flex gap-1">
          <span className="w-2 h-2 bg-green-400 rounded-full animate-bounce" 
                style={{ animationDelay: '0ms' }} />
          <span className="w-2 h-2 bg-green-400 rounded-full animate-bounce" 
                style={{ animationDelay: '150ms' }} />
          <span className="w-2 h-2 bg-green-400 rounded-full animate-bounce" 
                style={{ animationDelay: '300ms' }} />
        </div>
        <span className="text-sm text-gray-500">Thinking...</span>
      </div>
    </div>
  </div>
)}
```

---

## 5.10 Feedback Modal

**File:** `frontend/src/components/FeedbackModal.jsx`

```jsx
export default function FeedbackModal({ 
  isOpen, 
  onClose, 
  onSubmit, 
  conversationSummary 
}) {
  const [rating, setRating] = useState(null)
  const [suggestion, setSuggestion] = useState('')

  const handleSubmit = async () => {
    await onSubmit({ rating, suggestion })
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl">
        <h3 className="text-xl font-semibold mb-4">How was your experience?</h3>
        
        {/* Rating buttons */}
        <div className="flex justify-center gap-4 mb-6">
          {['bad', 'average', 'good'].map((r) => (
            <button
              key={r}
              onClick={() => setRating(r)}
              className={`px-6 py-3 rounded-xl border-2 transition-all
                ${rating === r 
                  ? 'border-green-500 bg-green-50 text-green-700' 
                  : 'border-gray-200 hover:border-green-300'
                }`}
            >
              {r === 'bad' && '😞'}
              {r === 'average' && '😐'}
              {r === 'good' && '😊'}
              <span className="ml-2 capitalize">{r}</span>
            </button>
          ))}
        </div>
        
        {/* Suggestion textarea */}
        <textarea
          value={suggestion}
          onChange={(e) => setSuggestion(e.target.value)}
          placeholder="Any suggestions for improvement?"
          className="w-full border rounded-xl p-3 mb-4"
          rows={3}
        />
        
        {/* Submit button */}
        <button
          onClick={handleSubmit}
          disabled={!rating}
          className="w-full bg-green-600 text-white py-3 rounded-xl 
                     hover:bg-green-700 disabled:opacity-50"
        >
          Submit Feedback
        </button>
      </div>
    </div>
  )
}
```

---

## 5.11 Docker Configuration

**File:** `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start dev server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

### Running with Docker

```bash
# Build and run
docker build -t stirling-frontend ./frontend
docker run -p 3000:3000 stirling-frontend

# Or use docker-compose (if configured)
docker-compose up frontend
```

---

## 5.12 TailwindCSS Configuration

**File:** `frontend/tailwind.config.js`

```javascript
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      animation: {
        'fadeIn': 'fadeIn 0.3s ease-out',
        'fadeInLogo': 'fadeInLogo 0.5s ease-out',
        'slideUp': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInLogo: {
          '0%': { opacity: '0', transform: 'scale(0.8)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
```

---

## 5.13 Component Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    COMPONENT MOUNT                              │
│                                                                 │
│  1. useState initializes all state                             │
│  2. useEffect runs (focus input if open)                       │
│  3. Component renders with empty messages                      │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USER OPENS CHAT                              │
│                                                                 │
│  1. setIsOpen(true)                                            │
│  2. useEffect triggers → inputRef.current.focus()              │
│  3. Welcome screen shown (messages.length === 0)               │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USER SENDS MESSAGE                           │
│                                                                 │
│  1. handleSendMessage() called                                 │
│  2. User message added to state (optimistic)                   │
│  3. setIsLoading(true) → loading indicator shown               │
│  4. axios.post() to backend                                    │
│  5. Response received → bot message added                      │
│  6. setIsLoading(false) → loading hidden                       │
│  7. inputRef.current.focus() → ready for next message          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USER CLOSES CHAT                             │
│                                                                 │
│  1. handleEndChat() called                                     │
│  2. POST to /api/conversation/{id}/end                         │
│  3. setShowFeedback(true) → FeedbackModal shown                │
│  4. User submits rating                                        │
│  5. POST to /api/feedback                                      │
│  6. setIsOpen(false) → chat closed                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5.14 Code Reading Exercise

### Exercise 1: Trace Message Flow

Open `frontend/src/components/ChatWidget.jsx` and:
1. Find `handleSendMessage()` function
2. Trace how user message is added to state
3. Find where API call is made
4. See how bot response is added

### Exercise 2: Understand Rendering

In `ChatWidget.jsx`, find:
1. The `messages.map()` that renders all messages
2. How user vs assistant messages are styled differently
3. How sources are rendered with links

### Exercise 3: Test the UI

1. Open http://localhost:3000
2. Open browser DevTools (F12)
3. Go to Network tab
4. Send a message and observe the API call
5. Check the request/response payloads

---

## 🎉 Congratulations!

You've completed the Stirling Chat Education Guide!

## Summary of What You Learned

| Part | Topic |
|------|-------|
| **1** | Project architecture and 3-agent design |
| **2** | PostgreSQL, pgvector, Docker setup |
| **3** | FastAPI endpoints and request flow |
| **4** | RAG system, embeddings, Claude integration |
| **5** | React components, state management, UI |

## Next Steps

1. **Modify the chatbot** - Try changing the greeting message
2. **Add a new feature** - Maybe a "clear chat" button
3. **Improve the UI** - Add dark mode support
4. **Enhance the RAG** - Experiment with different prompts
5. **Deploy it** - See the deployment tutorial

---

## Quick Reference

| Component | File | Purpose |
|-----------|------|---------|
| ChatWidget | `ChatWidget.jsx` | Main chat UI |
| FeedbackModal | `FeedbackModal.jsx` | Rating collection |
| Config | `config.js` | API endpoints |
| Styles | `index.css` | Global CSS + Tailwind |
| Build | `vite.config.js` | Vite configuration |
| Container | `Dockerfile` | Docker setup |

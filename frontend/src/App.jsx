import { useState, useEffect } from 'react'
import StirlingHomepage from './components/StirlingHomepage'
import ChatWidget from './components/ChatWidget'
import DisclaimerModal from './components/DisclaimerModal'
import { X } from 'lucide-react'

const CHAT_HINT_KEY = 'stirling_chat_hint_dismissed'

function App() {
  const [isChatOpen, setIsChatOpen] = useState(false)
  const [showChatHint, setShowChatHint] = useState(false)

  useEffect(() => {
    const dismissed = localStorage.getItem(CHAT_HINT_KEY)
    const disclaimerAccepted = localStorage.getItem('stirling_disclaimer_accepted')
    if (!dismissed && disclaimerAccepted) {
      const timer = setTimeout(() => setShowChatHint(true), 2500)
      return () => clearTimeout(timer)
    }
  }, [])

  const dismissChatHint = () => {
    localStorage.setItem(CHAT_HINT_KEY, 'true')
    setShowChatHint(false)
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="bg-amber-500 text-black text-center py-2.5 px-4 font-semibold text-sm sm:text-base shadow-md sticky top-0 z-50">
        ⚠️ <strong>DISCLAIMER:</strong> Independent academic research project — not an official University of Stirling website.
      </div>

      <DisclaimerModal />

      <StirlingHomepage />

      <ChatWidget onOpenChange={setIsChatOpen} />

      {showChatHint && !isChatOpen && (
        <div className="fixed bottom-20 right-4 sm:bottom-24 sm:right-6 z-30 flex items-center gap-2 max-w-[calc(100vw-2rem)]">
          <button
            type="button"
            onClick={() => window.dispatchEvent(new CustomEvent('openChatWidget'))}
            className="flex items-center gap-2 bg-[#006938] text-white pl-4 pr-3 py-2.5 rounded-xl shadow-lg text-sm font-semibold hover:bg-[#005530] transition-colors"
          >
            Try the AI chat
            <span aria-hidden>→</span>
          </button>
          <button
            type="button"
            onClick={dismissChatHint}
            className="p-2 rounded-full bg-white border border-gray-200 text-gray-500 shadow-md hover:bg-gray-50"
            aria-label="Dismiss hint"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}

export default App

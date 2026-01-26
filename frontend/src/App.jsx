import { useState } from 'react'
import StirlingHomepage from './components/StirlingHomepage'
import ChatWidget from './components/ChatWidget'
import DisclaimerModal from './components/DisclaimerModal'

function App() {
  const [isChatOpen, setIsChatOpen] = useState(false)

  return (
    <div className="min-h-screen bg-white">
      {/* Permanent Research Disclaimer Banner - Always visible at top */}
      <div className="bg-amber-500 text-black text-center py-3 px-4 font-bold text-lg shadow-md">
        ⚠️ <strong>DISCLAIMER:</strong> This is an independent academic research project for research purposes only. This is NOT an official University of Stirling website.
      </div>
      
      {/* Academic Research Disclaimer Modal - Shows on first visit only */}
      <DisclaimerModal />
      
      {/* Stirling University Homepage Clone */}
      <StirlingHomepage />
      
      {/* Chat Widget (Bottom Right Corner) */}
      <ChatWidget onOpenChange={setIsChatOpen} />

      {/* Blinking Arrow Pointing to Chat Widget - Only visible when chat is closed */}
      {!isChatOpen && (
        <div className="fixed bottom-24 right-6 z-[9998] flex items-center gap-2 animate-bounce">
          <div className="bg-[#006938] text-white px-3 py-2 rounded-lg shadow-lg text-sm font-semibold whitespace-nowrap">
            Try our AI Chat! →
          </div>
          <div className="text-4xl animate-pulse">👇</div>
        </div>
      )}

      {/* Custom CSS for blinking animation */}
      <style>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0.3; }
        }
        .animate-blink {
          animation: blink 1s infinite;
        }
      `}</style>
    </div>
  )
}

export default App

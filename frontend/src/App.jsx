import { useState } from 'react'
import StirlingHomepage from './components/StirlingHomepage'
import ChatWidget from './components/ChatWidget'
import DisclaimerModal from './components/DisclaimerModal'

function App() {
  return (
    <div className="min-h-screen bg-white">
      {/* Academic Research Disclaimer Modal - Shows on first visit only */}
      <DisclaimerModal />
      
      {/* Stirling University Homepage Clone */}
      <StirlingHomepage />
      
      {/* Chat Widget (Bottom Right Corner) */}
      <ChatWidget />
    </div>
  )
}

export default App

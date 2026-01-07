import { useState } from 'react'
import StirlingHomepage from './components/StirlingHomepage'
import ChatWidget from './components/ChatWidget'

function App() {
  return (
    <div className="min-h-screen bg-white">
      {/* Stirling University Homepage Clone */}
      <StirlingHomepage />
      
      {/* Chat Widget (Bottom Right Corner) */}
      <ChatWidget />
    </div>
  )
}

export default App

import { useState, useRef, useEffect } from 'react'
import { MessageCircle, X, Send, GraduationCap, ExternalLink, Minimize2, Maximize2, BookOpen, DollarSign, FileText, Home, Award, Building2, Globe, FileQuestion } from 'lucide-react'
import axios from 'axios'
import { API_ENDPOINTS, CHAT_CONFIG } from '../config'
import FeedbackModal from './FeedbackModal'

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [messages, setMessages] = useState([])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)
  const [showFeedback, setShowFeedback] = useState(false)
  const [conversationSummary, setConversationSummary] = useState(null)
  
  const messagesEndRef = useRef(null)
  const messagesContainerRef = useRef(null)
  const lastMessageRef = useRef(null)
  const inputRef = useRef(null)

  // Smart scroll: scroll to top of new assistant message, or bottom for user messages
  const scrollToNewMessage = (isUserMessage = false) => {
    setTimeout(() => {
      if (isUserMessage) {
        // For user messages, scroll to bottom so they see their message
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      } else {
        // For assistant messages, scroll to the TOP of the new message
        if (lastMessageRef.current) {
          lastMessageRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      }
    }, CHAT_CONFIG.AUTO_SCROLL_DELAY)
  }

  // Scroll to bottom when user sends a message or when loading starts
  useEffect(() => {
    if (isLoading) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [isLoading])

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && !isMinimized && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen, isMinimized])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage = inputMessage.trim()
    setInputMessage('')

    // Add user message to UI
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage,
      timestamp: new Date()
    }])
    
    // Scroll to bottom for user message
    scrollToNewMessage(true)

    setIsLoading(true)

    try {
      const response = await axios.post(API_ENDPOINTS.CHAT, {
        message: userMessage,
        session_id: sessionId
      })

      const data = response.data

      // Update session ID if new
      if (!sessionId) {
        setSessionId(data.session_id)
      }

      // Add bot response to UI
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
        suggested_questions: data.suggested_questions || [],
        timestamp: new Date()
      }])
      
      // Scroll to TOP of assistant message so user can read from beginning
      setTimeout(() => scrollToNewMessage(false), 100)

    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        isError: true
      }])
    } finally {
      setIsLoading(false)
      // Auto-focus input after bot responds so user can continue typing
      setTimeout(() => {
        if (inputRef.current) {
          inputRef.current.focus()
        }
      }, 100)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  // Helper function to render formatted text (bold and links)
  // Unified function to normalize all malformed text patterns from LLM
  const normalizeMalformedText = (text) => {
    if (!text) return text;
    
    let processedText = text;
    
    // Fix 1: Multiple opening brackets [[[text](url) or [[text](url) -> [text](url)
    processedText = processedText.replace(/\[\[+/g, '[');
    
    // Fix 2: Comprehensive orphaned bracket removal
    // Catches ALL cases where [ appears before a proper markdown link
    // Pattern: "[text [Link](url)" or "[ [Link](url)" -> "[Link](url)"
    processedText = processedText.replace(/\[([^\[\]]*?)\s*(\[[^\]]+\]\(https?:\/\/[^\s\)]+\))/g, (match, beforeLink, link) => {
      const cleanBefore = beforeLink.trim();
      return cleanBefore ? (cleanBefore + ' ' + link) : link;
    });
    
    // Fix 3: Remove standalone [ immediately followed by proper link
    // Pattern: "[[Link](url)" -> "[Link](url)"
    processedText = processedText.replace(/\[(?=\[[^\]]+\]\(https?:\/\/[^\s\)]+\))/g, '');
    
    // Fix 4: Missing opening bracket - Text](url) -> [Text](url)
    processedText = processedText.replace(/([A-Za-z0-9\s\(\)\-\'\"]+)\]\((https?:\/\/[^\s\)]+)\)/g, (match, linkText, url) => {
      const trimmedText = linkText.trim();
      if (trimmedText && !match.startsWith('[')) {
        return `[${trimmedText}](${url})`;
      }
      return match;
    });
    
    // Fix 5: Remove any remaining standalone [ not part of valid link
    processedText = processedText.replace(/\[(?![^\]]*\]\()(?!\[)/g, '');
    
    // Fix 6: Clean up multiple spaces that may result from replacements
    processedText = processedText.replace(/\s{2,}/g, ' ').trim();
    
    return processedText;
  };

  const renderFormattedText = (text, messageRole = 'assistant') => {
    if (!text) return text;
    
    // Pre-process: Fix malformed link patterns using unified function
    let processedText = normalizeMalformedText(text);
    
    // Process the text to find all matches and their positions
    const elements = [];
    let lastIndex = 0;
    let match;
    
    // Determine link/email styling based on message role
    const isUserMessage = messageRole === 'user';
    const linkClass = isUserMessage 
      ? "inline-flex items-center gap-1 text-white hover:text-green-100 underline decoration-white/60 underline-offset-2 font-medium transition-colors hover:decoration-white"
      : "inline-flex items-center gap-1 text-green-600 hover:text-green-700 underline decoration-green-400/60 underline-offset-2 font-medium transition-colors hover:decoration-green-600";
    
    // Create a combined regex to find patterns: bold, links, emails, and phone numbers
    // Email: word@word.word format
    // Phone: +44 followed by digits with optional spaces, or UK format numbers
    const combinedRegex = /(\*\*[^*]+\*\*|\[[^\]]+\]\(https?:\/\/[^\s\)]+\/?[^\s\)]*\)|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}|\+44\s?[\d\s]{10,13})/g;
    
    while ((match = combinedRegex.exec(processedText)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        elements.push(processedText.slice(lastIndex, match.index));
      }
      
      const matchedText = match[0];
      
      // Check if it's an email address
      const emailMatch = matchedText.match(/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/);
      if (emailMatch) {
        elements.push(
          <a 
            key={`email-${match.index}`}
            href={`mailto:${matchedText}`}
            className={linkClass}
          >
            {matchedText}
          </a>
        );
        lastIndex = match.index + matchedText.length;
        continue;
      }
      
      // Check if it's a phone number
      const phoneMatch = matchedText.match(/^\+44\s?[\d\s]{10,13}$/);
      if (phoneMatch) {
        const cleanPhone = matchedText.replace(/\s/g, '');
        elements.push(
          <a 
            key={`phone-${match.index}`}
            href={`tel:${cleanPhone}`}
            className={linkClass}
          >
            {matchedText}
          </a>
        );
        lastIndex = match.index + matchedText.length;
        continue;
      }
      
      // Check if it's a link - more permissive regex for URL matching
      const linkMatch = matchedText.match(/^\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)/);
      if (linkMatch) {
        // Clean link text: remove any leading/trailing brackets from malformed LLM output
        const cleanLinkText = linkMatch[1].replace(/^\[+/, '').replace(/\]+$/, '');
        elements.push(
          <a 
            key={`link-${match.index}`}
            href={linkMatch[2]}
            target="_blank"
            rel="noopener noreferrer"
            className={linkClass}
          >
            {cleanLinkText}
            <svg className="w-3 h-3 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        );
      }
      // Check if it's bold
      else if (matchedText.startsWith('**') && matchedText.endsWith('**')) {
        const innerText = matchedText.slice(2, -2);
        // Check if the bold text contains a link: **[text](url)**
        const innerLinkMatch = innerText.match(/^\[([^\]]+)\]\((https?:\/\/[^\s\)]+)\)$/);
        if (innerLinkMatch) {
          // Clean link text: remove any leading/trailing brackets from malformed LLM output
          const cleanBoldLinkText = innerLinkMatch[1].replace(/^\[+/, '').replace(/\]+$/, '');
          // It's a bold link - render as bold link
          const boldLinkClass = isUserMessage
            ? "inline-flex items-center gap-1 text-white hover:text-green-100 underline decoration-white/60 underline-offset-2 font-semibold transition-colors hover:decoration-white"
            : "inline-flex items-center gap-1 text-green-600 hover:text-green-700 underline decoration-green-400/60 underline-offset-2 font-semibold transition-colors hover:decoration-green-600";
          elements.push(
            <a 
              key={`bold-link-${match.index}`}
              href={innerLinkMatch[2]}
              target="_blank"
              rel="noopener noreferrer"
              className={boldLinkClass}
            >
              {cleanBoldLinkText}
              <svg className="w-3 h-3 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
            </a>
          );
        } else {
          // Regular bold text
          elements.push(
            <strong key={`bold-${match.index}`} className="font-semibold">
              {innerText}
            </strong>
          );
        }
      }
      
      lastIndex = match.index + matchedText.length;
    }
    
    // Add remaining text
    if (lastIndex < processedText.length) {
      elements.push(processedText.slice(lastIndex));
    }
    
    return elements.length > 0 ? elements : text;
  };
  
  // Alias for backward compatibility
  const renderInlineBold = renderFormattedText;

  const handleEndChat = async () => {
    if (!sessionId) {
      setIsOpen(false)
      return
    }

    try {
      const response = await axios.post(API_ENDPOINTS.END_CONVERSATION(sessionId))
      setConversationSummary(response.data)
      setShowFeedback(true)
    } catch (error) {
      console.error('End conversation error:', error)
      setShowFeedback(true)
    }
  }

  const handleFeedbackSubmit = () => {
    setMessages([])
    setSessionId(null)
    setShowFeedback(false)
    setConversationSummary(null)
    setIsOpen(false)
  }

  const handleFeedbackSkip = () => {
    setMessages([])
    setSessionId(null)
    setShowFeedback(false)
    setConversationSummary(null)
    setIsOpen(false)
  }

  // Typing indicator component
  const TypingIndicator = () => (
    <div className="flex justify-start animate-fadeIn">
      <div className="bg-white rounded-2xl px-5 py-4 shadow-md border border-gray-100 max-w-[85%]">
        <div className="flex items-center space-x-3">
          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-green-600 shadow-sm">
            <GraduationCap className="w-4 h-4 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium text-gray-700">Assistant is typing</span>
            <div className="flex space-x-1 mt-1">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
              <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
              <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Floating Chat Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 bg-gradient-to-br from-green-600 to-green-700 text-white p-4 sm:p-5 rounded-full shadow-2xl hover:shadow-green-500/25 hover:scale-105 transition-all duration-300 z-50 group"
          aria-label="Open chat"
        >
          <div className="relative">
            <MessageCircle className="w-6 h-6 sm:w-7 sm:h-7 group-hover:scale-110 transition-transform" />
            {/* Online indicator - positioned further from icon */}
            <span className="absolute -top-2 -right-2 w-3 h-3 bg-green-400 rounded-full animate-pulse border-2 border-white"></span>
          </div>
        </button>
      )}

      {/* Chat Window - Responsive with Fullscreen Support */}
      {isOpen && !isMinimized && (
        <div className={`fixed bg-white flex flex-col z-50 overflow-hidden animate-slideUp transition-all duration-300 ease-in-out ${
          isFullscreen 
            ? 'inset-0 rounded-none border-0 shadow-none' 
            : 'inset-4 sm:inset-auto sm:bottom-6 sm:right-6 sm:w-[420px] sm:h-[650px] rounded-2xl shadow-2xl border border-gray-200'
        }`}>
          
          {/* Header - Premium Design */}
          <div className="bg-gradient-to-r from-green-600 via-green-600 to-green-700 text-white px-5 py-4 flex items-center justify-between relative overflow-hidden">
            {/* Background pattern */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-0 right-0 w-32 h-32 bg-white rounded-full -translate-y-1/2 translate-x-1/2"></div>
              <div className="absolute bottom-0 left-0 w-24 h-24 bg-white rounded-full translate-y-1/2 -translate-x-1/2"></div>
            </div>
            
            <div className="flex items-center space-x-3 relative z-10">
              {/* Logo appears with fade when chat starts */}
              {messages.length > 0 && (
                <div className="relative animate-fadeInLogo">
                  <div className="flex items-center justify-center w-10 h-10 rounded-full bg-white/20 backdrop-blur-sm overflow-hidden">
                    <img src="/images/stirling round logo.png" alt="Stirling" className="w-10 h-10 object-cover" />
                  </div>
                  <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-300 rounded-full border-2 border-green-600"></span>
                </div>
              )}
              <div className="flex items-center space-x-2">
                <h3 className="font-semibold text-base tracking-tight">Stirling Assistant</h3>
                {messages.length === 0 && <span className="w-2.5 h-2.5 bg-green-300 rounded-full animate-pulse"></span>}
              </div>
            </div>
            
            <div className="flex items-center space-x-1 relative z-10">
              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                className="hover:bg-white/20 p-2 rounded-lg transition-colors"
                aria-label={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
                title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}
              >
                {isFullscreen ? <Minimize2 className="w-5 h-5" /> : <Maximize2 className="w-5 h-5" />}
              </button>
              <button
                onClick={handleEndChat}
                className="hover:bg-white/20 p-2 rounded-lg transition-colors"
                aria-label="Close chat"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-4 bg-gradient-to-b from-gray-50 to-white">
            
            {/* Welcome Message */}
            {messages.length === 0 && (
              <div className="text-center py-8 animate-fadeIn">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-green-100 to-green-200 mb-4 shadow-lg overflow-hidden">
                  <img src="/images/stirling round logo.png" alt="Stirling" className="w-16 h-16 object-cover" />
                </div>
                <h4 className="text-lg font-semibold text-gray-800 mb-2">Welcome to the University of Stirling!</h4>
                <p className="text-gray-600 text-sm max-w-xs mx-auto leading-relaxed">
                  I'm here to help you explore courses, understand requirements, and guide your journey.
                </p>
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {[
                    { label: 'Next Intake', query: 'When is the next intake?' },
                    { label: 'Entry Requirements', query: 'What are the entry requirements?' },
                    { label: 'Scholarships', query: 'What scholarships are available?' },
                    { label: 'How to Apply', query: 'How do I apply?' },
                    { label: 'Campus Life', query: 'Tell me about campus life' }
                  ].map((item) => (
                    <button
                      key={item.label}
                      onClick={() => setInputMessage(item.query)}
                      className="px-4 py-2 bg-white border border-gray-200 rounded-full text-sm text-gray-700 hover:border-green-500 hover:text-green-600 hover:bg-green-50 transition-all shadow-sm"
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Message List */}
            {messages.map((message, index) => {
              // Check if this is the last assistant message
              const isLastAssistantMessage = message.role === 'assistant' && 
                index === messages.length - 1;
              
              return (
              <div
                key={index}
                ref={isLastAssistantMessage ? lastMessageRef : null}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
              >
                <div
                  className={`max-w-[88%] rounded-2xl transition-all ${
                    message.role === 'user'
                      ? 'bg-gradient-to-br from-green-600 to-green-700 text-white px-5 py-3.5 shadow-lg shadow-green-500/20'
                      : message.isError
                      ? 'bg-red-50 text-red-800 px-5 py-4 border border-red-200 shadow-md'
                      : 'bg-white text-gray-800 px-5 py-4 shadow-md border border-gray-100'
                  }`}
                >
                  {/* Assistant Avatar for bot messages */}
                  {message.role === 'assistant' && !message.isError && (
                    <div className="flex items-center space-x-2 mb-3 pb-2 border-b border-gray-100">
                      <div className="w-6 h-6 rounded-full bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center">
                        <GraduationCap className="w-3.5 h-3.5 text-white" />
                      </div>
                      <span className="text-xs font-semibold text-green-700">Stirling Assistant</span>
                    </div>
                  )}

                  {/* Message Content */}
                  <div className={`text-[15px] leading-relaxed break-words ${message.role === 'user' ? 'text-white' : 'text-gray-700'}`}>
                    {message.content.split('\n').map((line, i) => {
                      // Normalize malformed text using unified function
                      let trimmedLine = normalizeMalformedText(line.trim());
                      
                      if (!trimmedLine) {
                        return <div key={i} className="h-3" />;
                      }
                      
                      // Heading
                      if (trimmedLine.startsWith('**') && (trimmedLine.endsWith('**') || trimmedLine.endsWith(':**'))) {
                        const headingText = trimmedLine.replace(/\*\*/g, '');
                        return (
                          <p key={i} className={`font-bold mt-4 mb-2 ${message.role === 'user' ? 'text-white' : 'text-gray-900'}`}>
                            {headingText}
                          </p>
                        );
                      }
                      
                      // Numbered list
                      const numberedMatch = trimmedLine.match(/^(\d+)\.\s+(.+)$/);
                      if (numberedMatch) {
                        return (
                          <div key={i} className="flex items-start my-1.5 ml-1">
                            <span className={`font-bold mr-3 min-w-[24px] ${message.role === 'user' ? 'text-green-200' : 'text-green-600'}`}>
                              {numberedMatch[1]}.
                            </span>
                            <span className="flex-1">{renderInlineBold(numberedMatch[2], message.role)}</span>
                          </div>
                        );
                      }
                      
                      // Bullet point
                      const bulletMatch = trimmedLine.match(/^[•\-\*]\s+(.+)$/);
                      if (bulletMatch) {
                        return (
                          <div key={i} className="flex items-start my-1.5 ml-1">
                            <span className={`mr-3 text-lg leading-none ${message.role === 'user' ? 'text-green-200' : 'text-green-500'}`}>•</span>
                            <span className="flex-1">{renderInlineBold(bulletMatch[1], message.role)}</span>
                          </div>
                        );
                      }
                      
                      // Regular text
                      return (
                        <p key={i} className={i > 0 ? 'mt-2' : ''}>
                          {renderInlineBold(trimmedLine, message.role)}
                        </p>
                      );
                    })}
                  </div>
                  
                  {/* Related Pages - World-Class Design */}
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-100">
                      <div className="flex items-center gap-2 mb-3">
                        <BookOpen className="w-4 h-4 text-green-600" />
                        <span className="text-sm font-semibold text-gray-700">Related Pages</span>
                      </div>
                      <div className="space-y-2">
                        {message.sources.slice(0, 3).map((source, idx) => {
                          // Get category-specific icon
                          const getCategoryIcon = (category) => {
                            const iconClass = "w-4 h-4 text-green-600";
                            switch(category?.toLowerCase()) {
                              case 'courses': return <GraduationCap className={iconClass} />;
                              case 'fees': return <DollarSign className={iconClass} />;
                              case 'admissions': return <FileText className={iconClass} />;
                              case 'accommodation': return <Home className={iconClass} />;
                              case 'scholarships': return <Award className={iconClass} />;
                              case 'campus': return <Building2 className={iconClass} />;
                              case 'international': return <Globe className={iconClass} />;
                              default: return <FileQuestion className={iconClass} />;
                            }
                          };
                          
                          // Generate short path for display
                          const getShortPath = (url) => {
                            const path = url.replace('https://www.stir.ac.uk/', '').replace('https://stir.ac.uk/', '');
                            const segments = path.split('/').filter(Boolean);
                            return segments.slice(0, 2).join(' › ') || 'stir.ac.uk';
                          };
                          
                          return (
                            <a
                              key={idx}
                              href={source.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block p-3 bg-gradient-to-r from-gray-50 to-white hover:from-green-50 hover:to-white rounded-xl border border-gray-100 hover:border-green-200 hover:shadow-sm transition-all duration-200 group"
                            >
                              <div className="flex items-start gap-3">
                                <span className="flex-shrink-0 w-9 h-9 rounded-lg bg-green-50 group-hover:bg-green-100 flex items-center justify-center transition-colors">
                                  {getCategoryIcon(source.category)}
                                </span>
                                <div className="flex-1 min-w-0">
                                  <p className="font-medium text-gray-800 group-hover:text-green-700 transition-colors line-clamp-1">
                                    {source.title || 'University of Stirling'}
                                  </p>
                                  <p className="text-xs text-gray-400 mt-0.5 flex items-center gap-1">
                                    <span className="truncate">stir.ac.uk › {getShortPath(source.url)}</span>
                                  </p>
                                </div>
                                <ExternalLink className="w-4 h-4 text-gray-300 group-hover:text-green-500 flex-shrink-0 mt-0.5 transition-colors" />
                              </div>
                            </a>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  
                  {/* Quick Reply Buttons - Only show on last assistant message */}
                  {message.suggested_questions && message.suggested_questions.length > 0 && 
                   index === messages.length - 1 && message.role === 'assistant' && !isLoading && (
                    <div className="mt-4 pt-3 border-t border-gray-100">
                      <p className="text-xs text-gray-400 mb-2.5 font-medium uppercase tracking-wide">Continue exploring</p>
                      <div className="flex flex-col gap-2">
                        {message.suggested_questions.map((question, qIdx) => {
                          // Icon mapping for professional look
                          const getIcon = (iconName) => {
                            const icons = {
                              'award': '🏆', 'credit-card': '💳', 'receipt': '📋',
                              'clipboard': '📝', 'briefcase': '💼', 'clock': '⏰',
                              'globe': '🌐', 'send': '📤', 'calendar': '📅',
                              'layers': '📚', 'file': '📄', 'home': '🏠',
                              'shield': '🛡️', 'list': '📋', 'passport': '🛂',
                              'pound': '💷', 'activity': '⚡', 'map': '🗺️', 'heart': '❤️'
                            };
                            return icons[iconName] || '💬';
                          };
                          
                          return (
                            <button
                              key={qIdx}
                              onClick={() => {
                                setInputMessage(question.text);
                                setTimeout(() => inputRef.current?.focus(), 50);
                              }}
                              className="group flex items-center gap-3 px-4 py-3 bg-gradient-to-r from-gray-50 via-white to-gray-50 
                                         border border-gray-200 rounded-xl text-left text-sm text-gray-700 
                                         hover:border-green-400 hover:from-green-50 hover:via-white hover:to-green-50
                                         hover:text-green-700 hover:shadow-md hover:shadow-green-100
                                         transition-all duration-200 transform hover:-translate-y-0.5"
                            >
                              <span className="flex items-center justify-center w-8 h-8 rounded-lg bg-white 
                                              border border-gray-100 group-hover:border-green-200 
                                              group-hover:bg-green-50 transition-colors text-base shadow-sm">
                                {getIcon(question.icon)}
                              </span>
                              <span className="flex-1 font-medium leading-snug">{question.text}</span>
                              <svg className="w-4 h-4 text-gray-300 group-hover:text-green-500 transition-colors" 
                                   fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                              </svg>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                  
                  {/* Timestamp */}
                  <p className={`text-xs mt-3 ${message.role === 'user' ? 'text-green-200' : 'text-gray-400'}`}>
                    {new Date(message.timestamp).toLocaleTimeString([], { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </p>
                </div>
              </div>
            );
            })}

            {/* Typing Indicator */}
            {isLoading && <TypingIndicator />}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area - Premium Design */}
          <div className="p-4 sm:p-5 border-t border-gray-100 bg-white">
            <div className="flex items-center space-x-3">
              <div className="flex-1 relative">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message..."
                  maxLength={CHAT_CONFIG.MAX_MESSAGE_LENGTH}
                  className="w-full px-5 py-3.5 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent focus:bg-white transition-all text-[15px] placeholder-gray-400"
                  disabled={isLoading}
                />
              </div>
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
                className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-green-600 to-green-700 text-white rounded-xl hover:shadow-lg hover:shadow-green-500/30 hover:scale-105 transition-all disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:shadow-none"
                aria-label="Send message"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
            
            {/* Footer info */}
            <div className="flex items-center justify-center mt-3">
              <span className="text-[10px] text-gray-400 font-light tracking-wide">
                Developed by{' '}
                <a 
                  href="https://www.linkedin.com/in/thebaqarjafri/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-gray-500 hover:text-[#006938] transition-colors duration-200 font-medium"
                >
                  Baqar Jafri
                </a>
                , MSc AI Student
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Minimized Chat Bar */}
      {isOpen && isMinimized && (
        <div 
          onClick={() => setIsMinimized(false)}
          className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 bg-gradient-to-r from-green-600 to-green-700 text-white px-5 py-3 rounded-full shadow-xl cursor-pointer hover:shadow-2xl hover:scale-105 transition-all z-50 flex items-center space-x-3"
        >
          <div className="relative">
            <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center overflow-hidden">
              <img src="/images/stirling round logo.png" alt="Stirling" className="w-8 h-8 object-cover" />
            </div>
            <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-green-300 rounded-full border-2 border-green-600"></span>
          </div>
          <span className="font-medium">Stirling Assistant</span>
          <button
            onClick={(e) => { e.stopPropagation(); handleEndChat(); }}
            className="ml-2 hover:bg-white/20 p-1 rounded-full transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Feedback Modal */}
      {showFeedback && (
        <FeedbackModal
          sessionId={sessionId}
          conversationSummary={conversationSummary}
          onSubmit={handleFeedbackSubmit}
          onSkip={handleFeedbackSkip}
        />
      )}

      {/* Custom Animations */}
      <style>{`
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px) scale(0.95);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }
        
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-slideUp {
          animation: slideUp 0.3s ease-out forwards;
        }
        
        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out forwards;
        }
        
        @keyframes fadeInLogo {
          from {
            opacity: 0;
            transform: scale(0.8);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
        
        .animate-fadeInLogo {
          animation: fadeInLogo 0.4s ease-out forwards;
        }
      `}</style>
    </>
  )
}

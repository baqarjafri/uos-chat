import { useState } from 'react'
import { ThumbsDown, Meh, ThumbsUp, X, Loader2 } from 'lucide-react'
import axios from 'axios'
import { API_ENDPOINTS } from '../config'

export default function FeedbackModal({ sessionId, conversationSummary, onSubmit, onSkip, variant = 'overlay' }) {
  const [rating, setRating] = useState(null)
  const [showSuggestion, setShowSuggestion] = useState(false)
  const [suggestion, setSuggestion] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const isPanel = variant === 'panel'

  const handleSubmit = async () => {
    if (!rating) return

    setIsSubmitting(true)
    setError(null)

    try {
      await axios.post(API_ENDPOINTS.FEEDBACK, {
        session_id: sessionId,
        rating: rating,
        suggestion: showSuggestion ? suggestion : null
      })

      onSubmit()
    } catch (err) {
      console.error('Feedback submission error:', err)
      setError('Failed to submit feedback. Please try again.')
      setIsSubmitting(false)
    }
  }

  const ratingOptions = [
    { value: 'bad', label: 'Bad', icon: ThumbsDown, color: 'text-red-500', bgColor: 'bg-red-100', hoverColor: 'hover:bg-red-200' },
    { value: 'average', label: 'Average', icon: Meh, color: 'text-yellow-500', bgColor: 'bg-yellow-100', hoverColor: 'hover:bg-yellow-200' },
    { value: 'good', label: 'Good', icon: ThumbsUp, color: 'text-green-500', bgColor: 'bg-green-100', hoverColor: 'hover:bg-green-200' },
  ]

  const card = (
    <div
      className={`bg-white rounded-2xl shadow-2xl w-full p-6 ${
        isPanel ? 'max-w-md border border-gray-200' : 'max-w-md mx-4'
      }`}
      onClick={(e) => e.stopPropagation()}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-bold text-stirling-blue">Quick feedback (optional)</h3>
        <button
          onClick={onSkip}
          className="text-gray-400 hover:text-gray-600 transition p-1"
          aria-label="Close"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {conversationSummary && (
        <div className="mb-3 p-3 bg-gray-50 rounded-lg text-sm text-gray-600">
          <p>
            <strong>Duration:</strong> {Math.floor(conversationSummary.duration_seconds / 60)} min ·{' '}
            <strong>Messages:</strong> {conversationSummary.total_messages}
          </p>
        </div>
      )}

      <p className="text-sm text-gray-600 mb-4">
        Only shown when you choose to end a conversation. Skip anytime.
      </p>

      <div className="grid grid-cols-3 gap-2 mb-4">
        {ratingOptions.map((option) => {
          const Icon = option.icon
          const isSelected = rating === option.value

          return (
            <button
              key={option.value}
              onClick={() => setRating(option.value)}
              className={`p-3 rounded-lg border-2 transition-all ${
                isSelected
                  ? `${option.bgColor} border-current ${option.color}`
                  : `border-gray-200 ${option.hoverColor}`
              }`}
            >
              <Icon className={`w-6 h-6 mx-auto mb-1 ${isSelected ? option.color : 'text-gray-400'}`} />
              <p className={`text-xs font-semibold ${isSelected ? option.color : 'text-gray-600'}`}>
                {option.label}
              </p>
            </button>
          )
        })}
      </div>

      <label className="flex items-center space-x-2 cursor-pointer mb-3">
        <input
          type="checkbox"
          checked={showSuggestion}
          onChange={(e) => setShowSuggestion(e.target.checked)}
          className="w-4 h-4 text-stirling-blue rounded focus:ring-2 focus:ring-stirling-blue"
        />
        <span className="text-sm text-gray-700">Add a suggestion</span>
      </label>

      {showSuggestion && (
        <div className="mb-4">
          <textarea
            value={suggestion}
            onChange={(e) => setSuggestion(e.target.value)}
            placeholder="What could we do better?"
            rows={3}
            maxLength={2000}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-stirling-blue resize-none text-sm"
          />
        </div>
      )}

      {error && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="flex space-x-2">
        <button
          onClick={onSkip}
          className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg hover:bg-gray-50 transition text-sm font-medium"
          disabled={isSubmitting}
        >
          Skip
        </button>
        <button
          onClick={handleSubmit}
          disabled={!rating || isSubmitting}
          className="flex-1 px-4 py-2.5 bg-stirling-blue text-white rounded-lg hover:bg-blue-900 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center text-sm font-medium"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Sending…
            </>
          ) : (
            'Submit'
          )}
        </button>
      </div>
    </div>
  )

  if (isPanel) {
    return (
      <div
        className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-[60] flex justify-end pointer-events-none"
        aria-modal="true"
        role="dialog"
      >
        <div className="pointer-events-auto">{card}</div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100]">
      {card}
    </div>
  )
}

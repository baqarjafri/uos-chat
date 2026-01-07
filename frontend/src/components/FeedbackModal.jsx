import { useState } from 'react'
import { ThumbsDown, Meh, ThumbsUp, X, Loader2 } from 'lucide-react'
import axios from 'axios'
import { API_ENDPOINTS } from '../config'

export default function FeedbackModal({ sessionId, conversationSummary, onSubmit, onSkip }) {
  const [rating, setRating] = useState(null)
  const [showSuggestion, setShowSuggestion] = useState(false)
  const [suggestion, setSuggestion] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

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

      // Success
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

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100]">
      <div className="bg-white rounded-lg shadow-2xl max-w-md w-full mx-4 p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-stirling-blue">How was your experience?</h3>
          <button
            onClick={onSkip}
            className="text-gray-400 hover:text-gray-600 transition"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Conversation Summary */}
        {conversationSummary && (
          <div className="mb-4 p-3 bg-gray-50 rounded text-sm text-gray-600">
            <p>
              <strong>Duration:</strong> {Math.floor(conversationSummary.duration_seconds / 60)} minutes
            </p>
            <p>
              <strong>Messages:</strong> {conversationSummary.total_messages}
            </p>
          </div>
        )}

        <p className="text-gray-600 mb-6">
          Your feedback helps us improve the chatbot experience!
        </p>

        {/* Rating Buttons */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          {ratingOptions.map((option) => {
            const Icon = option.icon
            const isSelected = rating === option.value
            
            return (
              <button
                key={option.value}
                onClick={() => setRating(option.value)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  isSelected
                    ? `${option.bgColor} border-current ${option.color}`
                    : `border-gray-200 ${option.hoverColor}`
                }`}
              >
                <Icon className={`w-8 h-8 mx-auto mb-2 ${isSelected ? option.color : 'text-gray-400'}`} />
                <p className={`text-sm font-semibold ${isSelected ? option.color : 'text-gray-600'}`}>
                  {option.label}
                </p>
              </button>
            )
          })}
        </div>

        {/* Suggestion Checkbox */}
        <div className="mb-4">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showSuggestion}
              onChange={(e) => setShowSuggestion(e.target.checked)}
              className="w-4 h-4 text-stirling-blue rounded focus:ring-2 focus:ring-stirling-blue"
            />
            <span className="text-sm text-gray-700">I have suggestions for improvement</span>
          </label>
        </div>

        {/* Suggestion Textarea */}
        {showSuggestion && (
          <div className="mb-6">
            <textarea
              value={suggestion}
              onChange={(e) => setSuggestion(e.target.value)}
              placeholder="What could we do better?"
              rows={4}
              maxLength={2000}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-stirling-blue resize-none"
            />
            <p className="text-xs text-gray-500 mt-1">
              {suggestion.length}/2000 characters
            </p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-3">
          <button
            onClick={onSkip}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
            disabled={isSubmitting}
          >
            Skip
          </button>
          <button
            onClick={handleSubmit}
            disabled={!rating || isSubmitting}
            className="flex-1 px-4 py-2 bg-stirling-blue text-white rounded-lg hover:bg-blue-900 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Submitting...
              </>
            ) : (
              'Submit Feedback'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

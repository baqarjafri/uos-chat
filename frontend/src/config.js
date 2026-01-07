// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  HEALTH: `${API_BASE_URL}/health`,
  CHAT: `${API_BASE_URL}/api/chat`,
  CONVERSATION: (sessionId) => `${API_BASE_URL}/api/conversation/${sessionId}`,
  END_CONVERSATION: (sessionId) => `${API_BASE_URL}/api/conversation/${sessionId}/end`,
  FEEDBACK: `${API_BASE_URL}/api/feedback`,
};

// Chat Configuration
export const CHAT_CONFIG = {
  MAX_MESSAGE_LENGTH: 2000,
  TYPING_DELAY: 500,
  AUTO_SCROLL_DELAY: 100,
};

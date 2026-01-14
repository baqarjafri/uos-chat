// Error handling utilities for frontend
export class APIError extends Error {
    constructor(message, status, data) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.data = data;
    }
}

export const handleAPIError = (error) => {
    if (error.response) {
        // Server responded with error status
        const status = error.response.status;
        const message = error.response.data?.detail || 'Something went wrong';
        
        switch (status) {
            case 429:
                return 'Too many requests. Please wait a moment and try again.';
            case 500:
                return 'Server error. Please try again later.';
            case 503:
                return 'Service temporarily unavailable. Please try again later.';
            default:
                return message;
        }
    } else if (error.request) {
        // Network error
        return 'Network error. Please check your connection and try again.';
    } else {
        // Other error
        return error.message || 'An unexpected error occurred.';
    }
};

// Retry logic for failed requests
export const retryRequest = async (fn, maxRetries = 3, delay = 1000) => {
    for (let i = 0; i < maxRetries; i++) {
        try {
            return await fn();
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            
            // Wait before retrying (exponential backoff)
            await new Promise(resolve => setTimeout(resolve, delay * (i + 1)));
        }
    }
};

// Usage in API calls:
// try {
//     const response = await retryRequest(() => api.post('/chat', message));
//     return response.data;
// } catch (error) {
//     const errorMessage = handleAPIError(error);
//     throw new APIError(errorMessage, error.status, error.data);
// }

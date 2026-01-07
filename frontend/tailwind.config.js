/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Stirling University Official Brand Colors (from stir.ac.uk)
        'stirling-red': '#C8102E',      // Primary red - buttons, accents
        'stirling-navy': '#00205B',     // Dark navy - headers, primary text
        'stirling-blue': '#00205B',     // Alias for navy (compatibility)
        'stirling-gray': '#F5F5F5',     // Light gray - backgrounds
        'stirling-dark-gray': '#4A4A4A', // Dark gray - secondary text
        'stirling-green': '#006938',     // Official green for specific CTAs (from source)
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

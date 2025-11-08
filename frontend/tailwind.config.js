/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'google': '#4285F4',
        'dropbox': '#0061FF',
        'microsoft': '#00BCF2',
        'terabox': '#FF6B00',
        // OneClouds brand palette
        'oc-dark': '#0B132B',
        'oc-navy': '#1C2541',
        'oc-steel': '#3A506B',
        'oc-teal': '#5BC0BE',
        'oc-white': '#FFFFFF',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
}

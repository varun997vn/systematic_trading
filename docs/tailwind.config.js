/** @type {import('tailwindcss').Config} */
module.exports = {
    corePlugins: {
        preflight: false, // Disable Tailwind's reset to avoid conflicts with Docusaurus
    },
    content: [
        './src/**/*.{js,jsx,ts,tsx}',
        './docs/**/*.{md,mdx}',
    ],
    darkMode: ['class', '[data-theme="dark"]'], // Use Docusaurus's dark mode attribute
    theme: {
        extend: {
            colors: {
                // Primary Brand Colors
                primary: {
                    DEFAULT: '#0ea5e9',
                    dark: '#0284c7',
                    darker: '#0369a1',
                    darkest: '#075985',
                    light: '#38bdf8',
                    lighter: '#7dd3fc',
                    lightest: '#bae6fd',
                },
                // Trading-specific colors
                trading: {
                    green: '#10b981',
                    red: '#ef4444',
                    amber: '#f59e0b',
                    purple: '#8b5cf6',
                },
                // Background colors
                background: {
                    light: '#ffffff',
                    surface: '#f8fafc',
                    dark: '#0f172a',
                    'surface-dark': '#1e293b',
                },
            },
            fontFamily: {
                sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'sans-serif'],
                mono: ['JetBrains Mono', 'Fira Code', 'Courier New', 'monospace'],
            },
            spacing: {
                'navbar': '64px',
            },
            borderRadius: {
                'global': '0.5rem',
                'code': '0.375rem',
            },
        },
    },
    plugins: [],
}
/** @type {import('tailwindcss').Config} */
module.exports = {
	darkMode: ['class'],
	content: [
		'./pages/**/*.{ts,tsx}',
		'./components/**/*.{ts,tsx}',
		'./app/**/*.{ts,tsx}',
		'./src/**/*.{ts,tsx}',
	],
	theme: {
		container: {
			center: true,
			padding: '2rem',
			screens: {
				'2xl': '1400px',
			},
		},
		extend: {
			colors: {
				border: 'hsl(var(--border))',
				input: 'hsl(var(--input))',
				ring: 'hsl(var(--ring))',
				background: 'hsl(var(--background))',
				foreground: 'hsl(var(--foreground))',
				primary: {
					50: '#0F2347',
					100: '#1A3564',
					500: '#4C8DFF',
					600: '#6AA3FF',
					700: '#85B8FF',
					DEFAULT: '#4C8DFF',
					foreground: '#FFFFFF',
				},
				secondary: {
					50: '#3A1A12',
					500: '#FF8A5C',
					600: '#FFA57D',
					DEFAULT: '#FF8A5C',
					foreground: '#FFFFFF',
				},
				neutral: {
					0: '#000000',
					50: '#0A0A0A',
					100: '#141414',
					200: '#1E1E1E',
					300: '#2A2A2A',
					400: '#71717A',
					500: '#A1A1AA',
					600: '#E4E4E7',
				},
				success: '#10B981',
				warning: '#F59E0B',
				error: '#EF4444',
				info: '#60A5FA',
				destructive: {
					DEFAULT: 'hsl(var(--destructive))',
					foreground: 'hsl(var(--destructive-foreground))',
				},
				muted: {
					DEFAULT: 'hsl(var(--muted))',
					foreground: 'hsl(var(--muted-foreground))',
				},
				popover: {
					DEFAULT: 'hsl(var(--popover))',
					foreground: 'hsl(var(--popover-foreground))',
				},
				card: {
					DEFAULT: 'hsl(var(--card))',
					foreground: 'hsl(var(--card-foreground))',
				},
			},
			fontFamily: {
				sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
				mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
			},
			fontSize: {
				hero: ['48px', { lineHeight: '1.1', fontWeight: '700' }],
				h1: ['32px', { lineHeight: '1.2', fontWeight: '700' }],
				h2: ['24px', { lineHeight: '1.3', fontWeight: '600' }],
				h3: ['20px', { lineHeight: '1.3', fontWeight: '600' }],
				'body-lg': ['18px', { lineHeight: '1.6', fontWeight: '400' }],
				body: ['16px', { lineHeight: '1.5', fontWeight: '400' }],
				small: ['14px', { lineHeight: '1.5', fontWeight: '400' }],
				caption: ['12px', { lineHeight: '1.4', fontWeight: '400' }],
			},
			spacing: {
				xs: '4px',
				sm: '8px',
				md: '16px',
				lg: '24px',
				xl: '32px',
				'2xl': '48px',
				'3xl': '64px',
				'4xl': '96px',
			},
			borderRadius: {
				sm: '4px',
				md: '8px',
				lg: '12px',
				xl: '16px',
				full: '9999px',
			},
			boxShadow: {
				card: '0 0 0 1px rgba(255,255,255,0.05), 0 4px 12px rgba(0,0,0,0.5)',
				'card-hover': '0 0 0 1px rgba(255,255,255,0.1), 0 8px 24px rgba(0,0,0,0.6)',
				'glow-primary': '0 0 20px rgba(76,141,255,0.4), 0 0 40px rgba(76,141,255,0.2)',
				'glow-secondary': '0 0 20px rgba(255,138,92,0.4), 0 0 40px rgba(255,138,92,0.2)',
				modal: '0 0 0 1px rgba(255,255,255,0.1), 0 24px 48px rgba(0,0,0,0.7)',
			},
			animation: {
				'accordion-down': 'accordion-down 0.2s ease-out',
				'accordion-up': 'accordion-up 0.2s ease-out',
				'pulse-glow': 'pulse-glow 2s infinite',
			},
			keyframes: {
				'accordion-down': {
					from: { height: 0 },
					to: { height: 'var(--radix-accordion-content-height)' },
				},
				'accordion-up': {
					from: { height: 'var(--radix-accordion-content-height)' },
					to: { height: 0 },
				},
				'pulse-glow': {
					'0%, 100%': { boxShadow: '0 0 20px rgba(255,138,92,0.4)' },
					'50%': { boxShadow: '0 0 30px rgba(255,138,92,0.6)' },
				},
			},
		},
	},
	plugins: [require('tailwindcss-animate')],
}

import { createTheme, alpha } from '@mui/material/styles';

// Define color palette
const colors = {
    primary: {
        main: '#3b82f6', // blue-500
        light: '#60a5fa', // blue-400
        dark: '#2563eb', // blue-600
    },
    secondary: {
        main: '#8b5cf6', // violet-500
        light: '#a78bfa', // violet-400
        dark: '#7c3aed', // violet-600
    },
    success: {
        main: '#10b981', // emerald-500
        light: '#34d399', // emerald-400
        dark: '#059669', // emerald-600
    },
    error: {
        main: '#ef4444', // red-500
        light: '#f87171', // red-400
        dark: '#dc2626', // red-600
    },
    warning: {
        main: '#f59e0b', // amber-500
        light: '#fbbf24', // amber-400
        dark: '#d97706', // amber-600
    },
    info: {
        main: '#06b6d4', // cyan-500
        light: '#22d3ee', // cyan-400
        dark: '#0891b2', // cyan-600
    },
    background: {
        default: '#0f172a', // slate-900
        paper: '#1e293b', // slate-800
    },
    text: {
        primary: '#f1f5f9', // slate-100
        secondary: '#94a3b8', // slate-400
    },
};

// Create theme
export const theme = createTheme({
    palette: {
        mode: 'dark',
        ...colors,
    },
    typography: {
        fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
        h1: {
            fontSize: '3rem',
            fontWeight: 700,
            letterSpacing: '-0.02em',
        },
        h2: {
            fontSize: '2.5rem',
            fontWeight: 700,
            letterSpacing: '-0.01em',
        },
        h3: {
            fontSize: '2rem',
            fontWeight: 600,
        },
        h4: {
            fontSize: '1.5rem',
            fontWeight: 600,
        },
        h5: {
            fontSize: '1.25rem',
            fontWeight: 600,
        },
        h6: {
            fontSize: '1rem',
            fontWeight: 600,
        },
        button: {
            textTransform: 'none',
            fontWeight: 600,
        },
    },
    shape: {
        borderRadius: 8,
    },
    components: {
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                    padding: '8px 16px',
                    fontSize: '0.875rem',
                },
                contained: {
                    boxShadow: 'none',
                    '&:hover': {
                        boxShadow: 'none',
                    },
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    backgroundImage: 'none',
                    border: `1px solid ${alpha(colors.text.secondary, 0.1)}`,
                },
            },
        },
        MuiCard: {
            styleOverrides: {
                root: {
                    backgroundImage: 'none',
                    border: `1px solid ${alpha(colors.text.secondary, 0.1)}`,
                },
            },
        },
        MuiTextField: {
            styleOverrides: {
                root: {
                    '& .MuiOutlinedInput-root': {
                        '& fieldset': {
                            borderColor: alpha(colors.text.secondary, 0.2),
                        },
                        '&:hover fieldset': {
                            borderColor: alpha(colors.text.secondary, 0.3),
                        },
                    },
                },
            },
        },
        MuiChip: {
            styleOverrides: {
                root: {
                    fontWeight: 500,
                },
            },
        },
        MuiTableCell: {
            styleOverrides: {
                root: {
                    borderBottom: `1px solid ${alpha(colors.text.secondary, 0.1)}`,
                },
                head: {
                    fontWeight: 600,
                    color: colors.text.primary,
                },
            },
        },
        MuiIconButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                },
            },
        },
        MuiSlider: {
            styleOverrides: {
                root: {
                    '& .MuiSlider-thumb': {
                        width: 16,
                        height: 16,
                    },
                },
            },
        },
    },
});

export default theme;
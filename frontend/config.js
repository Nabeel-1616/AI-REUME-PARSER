// Configuration for Resumify Frontend
const CONFIG = {
    // Updated for ap-south-1 region deployment
    API_BASE_URL: 'https://ol283os1h3.execute-api.ap-south-1.amazonaws.com/dev',

    // UI Configuration
    THEME: {
        colors: {
            primary: '#6366f1',    // Indigo
            secondary: '#f59e0b',  // Amber  
            accent: '#10b981',     // Emerald
            background: '#0f172a', // Slate 900
            surface: 'rgba(255, 255, 255, 0.04)',
            text: '#f8fafc'        // Slate 50
        },
        fonts: {
            heading: 'Sora, sans-serif',
            body: 'Inter, sans-serif'
        }
    },

    // Feature flags
    FEATURES: {
        enableAnalytics: true,
        enableReports: true,
        enableRealTimeUpdates: true
    },

    // Environment detection
    DEVELOPMENT_MODE: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
};

// Utility functions
function isDevelopmentMode() {
    return CONFIG.DEVELOPMENT_MODE;
}

// Make config available globally
window.RESUMIFY_CONFIG = CONFIG;
window.isDevelopmentMode = isDevelopmentMode;

// ==================== Authentication Logic ====================
const AUTH_API_URL = '/api/auth';

const auth = {
    token: localStorage.getItem('access_token'),
    user: JSON.parse(localStorage.getItem('user') || 'null'),

    async login(username, password) {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        try {
            const response = await fetch(`${AUTH_API_URL}/login`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await response.json();
            this.setSession(data.access_token, username);
            return true;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    },

    async register(username, password, fullName, email) {
        try {
            const response = await fetch(`${AUTH_API_URL}/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username,
                    password,
                    full_name: fullName,
                    email
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Registration failed');
            }

            return await response.json();
        } catch (error) {
            console.error('Registration error:', error);
            throw error;
        }
    },

    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        this.token = null;
        this.user = null;
        window.location.href = '/login.html';
    },

    setSession(token, username) {
        this.token = token;
        this.user = { username };
        localStorage.setItem('access_token', token);
        localStorage.setItem('user', JSON.stringify(this.user));
    },

    isAuthenticated() {
        return !!this.token;
    },

    // Helper to add auth header to requests
    getHeaders() {
        const headers = {};
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }
};

// Protect routes
function requireAuth() {
    if (!auth.isAuthenticated()) {
        window.location.href = '/login.html';
    }
}

// Make auth and requireAuth globally accessible
window.auth = auth;
window.requireAuth = requireAuth;

// Auto-check authentication when this script loads on index.html
// Only redirect if we're on the main application page (not on login page)
if (window.location.pathname === '/index.html') {
    requireAuth();
}

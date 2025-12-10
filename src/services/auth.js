import { authAPI } from './api';

// Store in memory (not localStorage) for guest mode
let guestMode = false;
let currentUsername = null;

const authService = {
  login: async (username, password) => {
    try {
      const response = await authAPI.login(username, password);
      const token = response.data.token;
      localStorage.setItem('authToken', token);
      localStorage.setItem('username', username);
      guestMode = false;
      currentUsername = username;
      return { success: true, user: { username, token } };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data || 'Login failed',
      };
    }
  },

  register: async (username, email, password, password2) => {
    try {
      await authAPI.register(username, email, password, password2);
      return { success: true };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data || 'Registration failed',
      };
    }
  },

  // New: Guest mode
  loginAsGuest: () => {
    guestMode = true;
    currentUsername = 'Guest';
    localStorage.removeItem('authToken');
    localStorage.removeItem('username');
    return { success: true, user: { username: 'Guest' } };
  },

  logout: () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('username');
    guestMode = false;
    currentUsername = null;
  },

  isAuthenticated: () => {
    return !!localStorage.getItem('authToken') || guestMode;
  },

  isGuest: () => {
    return guestMode && !localStorage.getItem('authToken');
  },

  getUsername: () => {
    return currentUsername || localStorage.getItem('username') || 'Guest';
  },

  getToken: () => {
    return localStorage.getItem('authToken');
  },

  // Initialize on app load
  initAuth: () => {
    const token = localStorage.getItem('authToken');
    const username = localStorage.getItem('username');
    if (token && username) {
      currentUsername = username;
      guestMode = false;
    }
  },
};

export default authService;

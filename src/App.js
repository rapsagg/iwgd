import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { applyTheme, themeService, darkTheme, lightTheme } from './utils/theme';
import authService from './services/auth';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Home from './pages/Home';
import CreatePost from './pages/CreatePost';
import PostDetail from './pages/PostDetail';
import './styles/variables.css';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(authService.isAuthenticated());
  const [theme, setTheme] = useState(themeService.getCurrentTheme());
  const [isDarkMode, setIsDarkMode] = useState(themeService.isDarkMode());

  useEffect(() => {
    const theme = themeService.getCurrentTheme();
    applyTheme(theme);
  }, []);

  const handleLogout = () => {
    authService.logout();
    setIsAuthenticated(false);
  };

  const handleThemeToggle = () => {
    const newTheme = themeService.toggleTheme();
    applyTheme(newTheme);
    setIsDarkMode(newTheme.name === 'dark');
  };

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  return (
    <Router>
      <div className="App">
        {isAuthenticated && (
          <Navbar
            onLogout={handleLogout}
            onThemeToggle={handleThemeToggle}
            isDarkMode={themeService.isDarkMode()}
          />
        )}
        <Routes>
          <Route
            path="/login"
            element={
              isAuthenticated ? (
                <Navigate to="/" replace />
              ) : (
                <Login onLoginSuccess={handleLoginSuccess} />
              )
            }
          />
          <Route
            path="/"
            element={
              isAuthenticated ? (
                <Home />
              ) : (
                <Navigate to="/login" replace />
              )
            }
          />
          <Route path="/" element={<Home />} />
          <Route path="/create/:topicId?" element={<CreatePost />} />
          <Route path="*" element={<Navigate to="/" replace />} />
          <Route path="/post/:postId" element={<PostDetail />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;

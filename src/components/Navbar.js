import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/auth';
import '../styles/Navbar.css';

function Navbar({ onLogout, onThemeToggle, isDarkMode }) {
  const navigate = useNavigate();
  const [showDropdown, setShowDropdown] = useState(false);
  const username = authService.getUsername();
  const isGuest = authService.isGuest();

  const handleLogout = () => {
    authService.logout();
    onLogout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Logo/Brand */}
        <div className="navbar-brand" onClick={() => navigate('/')}>
          <h2>Politics Forum</h2>
        </div>

        {/* Center - Search (placeholder for now) */}
        <div className="navbar-search">
          <input
            type="text"
            placeholder="Search posts, topics..."
            className="search-input"
          />
        </div>

        {/* Right - Theme toggle + User menu */}
        <div className="navbar-right">
          {/* Theme toggle */}
          <button
            className="btn-theme"
            onClick={onThemeToggle}
            title={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDarkMode ? '☀️' : '🌙'}
          </button>

          {/* User dropdown */}
          <div className="user-menu">
            <button
              className="btn-user"
              onClick={() => setShowDropdown(!showDropdown)}
            >
              👤 {username}
              {isGuest && <span className="guest-badge">Guest</span>}
            </button>

            {showDropdown && (
              <div className="dropdown-menu">
                {!isGuest && (
                  <>
                    <a href="#profile" className="dropdown-item">
                      👤 My Profile
                    </a>
                    <a href="#settings" className="dropdown-item">
                      ⚙️ Settings
                    </a>
                    <hr className="dropdown-divider" />
                  </>
                )}
                {isGuest && (
                  <>
                    <div className="dropdown-info">
                      You are browsing as a guest. <br />
                      <a href="#login" onClick={() => navigate('/login')} className="guest-link">
                        Login or register
                      </a>
                      to interact.
                    </div>
                    <hr className="dropdown-divider" />
                  </>
                )}
                <button
                  onClick={handleLogout}
                  className="dropdown-item logout-btn"
                >
                  🚪 {isGuest ? 'Exit Guest Mode' : 'Logout'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;

import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import { LogOut, User } from 'lucide-react';

const Navbar = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="navbar">
      <div className="navbar-content">
        <Link to="/" className="logo">
          QuizCanvas
        </Link>
        
        <ul className="nav-links">
          <li><Link to="/">Home</Link></li>
          <li><Link to="/faq">FAQ</Link></li>
          
          {isAuthenticated ? (
            <>
              <li><Link to="/dashboard">Dashboard</Link></li>
              <li><Link to="/upload">Upload Quiz</Link></li>
              <li>
                <Link to="/profile" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <User size={18} />
                  {user?.username || 'Profile'}
                </Link>
              </li>
              <li>
                <button 
                  onClick={handleLogout}
                  style={{ 
                    background: 'none', 
                    border: 'none', 
                    color: 'white', 
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    padding: '0.5rem 1rem',
                    borderRadius: '4px'
                  }}
                  onMouseOver={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.1)'}
                  onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
                >
                  <LogOut size={18} />
                  Logout
                </button>
              </li>
            </>
          ) : (
            <>
              <li><Link to="/login">Login</Link></li>
              <li><Link to="/register">Register</Link></li>
            </>
          )}
        </ul>
      </div>
    </nav>
  );
};

export default Navbar;
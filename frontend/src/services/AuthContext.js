import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Configure axios defaults - match Dashboard.js configuration
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://api.quizcanvas.xyz' 
  : 'http://localhost:8000';
  
axios.defaults.baseURL = API_BASE_URL;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user'); 
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  // Initialize authentication state
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const storedToken = localStorage.getItem('token');
        
        if (storedToken) {
          // Set token in axios headers first
          axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`;
          
          // Try to get stored user data
          const storedUser = localStorage.getItem('user');
          if (storedUser) {
            try {
              const userData = JSON.parse(storedUser);
              setUser(userData);
            } catch (error) {
              console.error('Error parsing stored user data:', error);
              // If stored user data is corrupted, try to verify token with backend
              try {
                const response = await axios.get('/api/dashboard/');
                if (response.data.success) {
                  // Token is valid, reconstruct user data from any available source
                  const userData = {
                    username: response.data.data?.user?.username || 'User',
                    email: response.data.data?.user?.email || '',
                    user_id: response.data.data?.user?.user_id || null
                  };
                  setUser(userData);
                  localStorage.setItem('user', JSON.stringify(userData));
                } else {
                  logout();
                }
              } catch (apiError) {
                console.error('Token verification failed:', apiError);
                logout();
              }
            }
          } else {
            // No stored user data, but we have a token - verify it
            try {
              const response = await axios.get('/api/dashboard/');
              if (response.data.success) {
                // Token is valid, reconstruct user data
                const userData = {
                  username: response.data.data?.user?.username || 'User',
                  email: response.data.data?.user?.email || '',
                  user_id: response.data.data?.user?.user_id || null
                };
                setUser(userData);
                localStorage.setItem('user', JSON.stringify(userData));
              } else {
                logout();
              }
            } catch (apiError) {
              console.error('Token verification failed:', apiError);
              logout();
            }
          }
        }
      } catch (error) {
        console.error('Error initializing auth:', error);
        logout();
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const login = async (username, password) => {
    try {
      setLoading(true);
      const response = await axios.post('/api/auth/login/', {
        username,
        password
      });
      
      if (response.data.success) {
        const { token: authToken, user_id, username: userName, email } = response.data.data;
        
        // Create user object from login response
        const userData = {
          user_id,
          username: userName,
          email
        };
        
        localStorage.setItem('token', authToken);
        localStorage.setItem('user', JSON.stringify(userData));
        setUser(userData);
        axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;
        
        return { success: true };
      } else {
        return { 
          success: false, 
          error: response.data.error || 'Login failed' 
        };
      }
    } catch (error) {
      console.error('Login failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.error || 'Login failed' 
      };
    } finally {
      setLoading(false);
    }
  };

  const register = async (username, email, password) => {
    try {
      setLoading(true);
      const response = await axios.post('/api/auth/register/', {
        username,
        email,
        password
      });
      
      if (response.data.success) {
        return { success: true, data: response.data };
      } else {
        return { 
          success: false, 
          error: response.data.error || 'Registration failed' 
        };
      }
    } catch (error) {
      console.error('Registration failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.error || 'Registration failed' 
      };
    } finally {
      setLoading(false);
    }
  };

  const value = {
    user,
    login,
    register,
    logout,
    loading,
    isAuthenticated: !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
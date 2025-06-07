import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import { Plus, BookOpen, BarChart3, Clock, Trash2 } from 'lucide-react';
import axios from 'axios';

const Dashboard = () => {
  const { user, isAuthenticated } = useAuth();
  const [quizzes, setQuizzes] = useState([]);
  const [recentAttempts, setRecentAttempts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    fetchDashboardData();
  }, [isAuthenticated, navigate]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // Fetch user's quizzes
      const quizzesResponse = await axios.get('/quizzes/');
      setQuizzes(quizzesResponse.data || []);
      
      // Fetch recent attempts
      const attemptsResponse = await axios.get('/quiz-attempts/recent/');
      setRecentAttempts(attemptsResponse.data || []);
      
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteQuiz = async (quizId) => {
    if (!window.confirm('Are you sure you want to delete this quiz? This action cannot be undone.')) {
      return;
    }

    try {
      await axios.delete(`/quizzes/${quizId}/`);
      setQuizzes(quizzes.filter(quiz => quiz.id !== quizId));
    } catch (error) {
      console.error('Failed to delete quiz:', error);
      setError('Failed to delete quiz');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="page">
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Welcome back, {user?.username}!</h1>
          <p style={{ color: '#7f8c8d', marginTop: '0.5rem' }}>
            Track your progress and continue learning
          </p>
        </div>
        <Link to="/upload" className="btn btn-primary">
          <Plus size={20} style={{ marginRight: '0.5rem' }} />
          Upload New Quiz
        </Link>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {/* Stats Overview */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div className="card" style={{ textAlign: 'center' }}>
          <BookOpen size={32} style={{ color: '#3498db', marginBottom: '0.5rem' }} />
          <h3 style={{ margin: '0.5rem 0' }}>{quizzes.length}</h3>
          <p style={{ color: '#7f8c8d', margin: 0 }}>Total Quizzes</p>
        </div>
        
        <div className="card" style={{ textAlign: 'center' }}>
          <Clock size={32} style={{ color: '#27ae60', marginBottom: '0.5rem' }} />
          <h3 style={{ margin: '0.5rem 0' }}>{recentAttempts.length}</h3>
          <p style={{ color: '#7f8c8d', margin: 0 }}>Recent Attempts</p>
        </div>
        
        <div className="card" style={{ textAlign: 'center' }}>
          <BarChart3 size={32} style={{ color: '#e74c3c', marginBottom: '0.5rem' }} />
          <h3 style={{ margin: '0.5rem 0' }}>
            {recentAttempts.length > 0 
              ? Math.round(recentAttempts.reduce((acc, attempt) => acc + (attempt.score || 0), 0) / recentAttempts.length)
              : 0}%
          </h3>
          <p style={{ color: '#7f8c8d', margin: 0 }}>Avg Score</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
        {/* My Quizzes */}
        <div>
          <h2 style={{ marginBottom: '1rem' }}>My Quizzes</h2>
          {quizzes.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
              <BookOpen size={48} style={{ color: '#bdc3c7', marginBottom: '1rem' }} />
              <h3 style={{ color: '#7f8c8d', marginBottom: '1rem' }}>No quizzes yet</h3>
              <p style={{ color: '#95a5a6', marginBottom: '2rem' }}>
                Upload your first quiz to get started
              </p>
              <Link to="/upload" className="btn btn-primary">
                Upload Quiz
              </Link>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: '1rem' }}>
              {quizzes.map(quiz => (
                <div key={quiz.id} className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <h3 style={{ marginBottom: '0.5rem' }}>
                        <Link 
                          to={`/quiz/${quiz.id}`}
                          style={{ textDecoration: 'none', color: '#2c3e50' }}
                        >
                          {quiz.title}
                        </Link>
                      </h3>
                      <p style={{ color: '#7f8c8d', marginBottom: '1rem' }}>
                        {quiz.description || 'No description provided'}
                      </p>
                      <div style={{ fontSize: '0.9rem', color: '#95a5a6' }}>
                        <span>{quiz.question_count || 0} questions</span>
                        {quiz.sections_count > 0 && (
                          <span> • {quiz.sections_count} sections</span>
                        )}
                        <span> • Created {formatDate(quiz.created_at)}</span>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeleteQuiz(quiz.id)}
                      className="btn btn-danger"
                      style={{ padding: '0.5rem', marginLeft: '1rem' }}
                      title="Delete quiz"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div>
          <h2 style={{ marginBottom: '1rem' }}>Recent Activity</h2>
          {recentAttempts.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
              <Clock size={32} style={{ color: '#bdc3c7', marginBottom: '1rem' }} />
              <p style={{ color: '#7f8c8d' }}>No recent activity</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: '1rem' }}>
              {recentAttempts.slice(0, 5).map(attempt => (
                <div key={attempt.id} className="card" style={{ padding: '1rem' }}>
                  <h4 style={{ marginBottom: '0.5rem', fontSize: '1rem' }}>
                    {attempt.quiz_title}
                  </h4>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ 
                      color: attempt.score >= 70 ? '#27ae60' : '#e74c3c',
                      fontWeight: 'bold'
                    }}>
                      {attempt.score}%
                    </span>
                    <span style={{ color: '#95a5a6', fontSize: '0.8rem' }}>
                      {formatDate(attempt.completed_at)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
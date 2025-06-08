import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import { BookOpen, Clock, BarChart3, PlayCircle } from 'lucide-react';
import axios from 'axios';

axios.defaults.baseURL = 'https://api.quizcanvas.xyz';

const QuizLanding = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, loading: authLoading } = useAuth();

  const [quiz, setQuiz] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [timerMinutes, setTimerMinutes] = useState('');

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    const fetchData = async () => {
      try {
        setLoading(true);
        const [detailsRes, statsRes] = await Promise.all([
          axios.get(`/api/quizzes/${id}/`),
          axios.get(`/api/quizzes/${id}/statistics/`)
        ]);

        if (detailsRes.data.success) {
          setQuiz(detailsRes.data.data.quiz);
        }
        if (statsRes.data.success) {
          setStats(statsRes.data.data);
        }
      } catch (err) {
        console.error('Failed to fetch quiz info:', err);
        setError('Failed to load quiz information');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id, isAuthenticated, authLoading, navigate]);

  const startQuiz = () => {
    const url = timerMinutes ? `/quiz/${id}/take?timer=${timerMinutes}` : `/quiz/${id}/take`;
    navigate(url);
  };

  if (authLoading || loading) {
    return (
      <div className="page">
        <div className="loading">
          <div className="spinner"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="error-message">{error}</div>
      </div>
    );
  }

  return (
    <div className="page">
      <h1>{quiz?.title}</h1>
      <p style={{ color: '#7f8c8d', marginBottom: '2rem' }}>{quiz?.description}</p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        <div className="card" style={{ textAlign: 'center' }}>
          <BookOpen size={32} style={{ color: '#3498db', marginBottom: '0.5rem' }} />
          <h3 style={{ margin: '0.5rem 0' }}>{quiz?.total_questions || 0}</h3>
          <p style={{ color: '#7f8c8d', margin: 0 }}>Questions</p>
        </div>

        <div className="card" style={{ textAlign: 'center' }}>
          <Clock size={32} style={{ color: '#27ae60', marginBottom: '0.5rem' }} />
          <h3 style={{ margin: '0.5rem 0' }}>{stats?.user_stats?.total_attempts || 0}</h3>
          <p style={{ color: '#7f8c8d', margin: 0 }}>Attempts</p>
        </div>

        <div className="card" style={{ textAlign: 'center' }}>
          <BarChart3 size={32} style={{ color: '#e74c3c', marginBottom: '0.5rem' }} />
          <h3 style={{ margin: '0.5rem 0' }}>{stats?.user_stats?.best_score || 0}%</h3>
          <p style={{ color: '#7f8c8d', margin: 0 }}>Best Score</p>
        </div>
      </div>

      <div className="card" style={{ textAlign: 'center' }}>
        <div style={{ marginBottom: '1rem' }}>
          <label htmlFor="timer" style={{ marginRight: '0.5rem' }}>Custom Timer (minutes):</label>
          <input
            id="timer"
            type="number"
            min="1"
            value={timerMinutes}
            onChange={(e) => setTimerMinutes(e.target.value)}
            style={{ width: '80px' }}
          />
        </div>
        <button onClick={startQuiz} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}>
          <PlayCircle size={16} />
          Start Quiz
        </button>
      </div>
    </div>
  );
};

export default QuizLanding;
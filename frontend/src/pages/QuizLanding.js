import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import { BookOpen, Clock, BarChart3, PlayCircle, TrendingUp, Edit2, X, Check } from 'lucide-react';
import axios from 'axios';

axios.defaults.baseURL = 'https://api.quizcanvas.xyz';

const QuizLanding = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, loading: authLoading } = useAuth();

  const [quiz, setQuiz] = useState(null);
  const [stats, setStats] = useState(null);
  const [masteryLevel, setMasteryLevel] = useState('Not Started');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [timerMinutes, setTimerMinutes] = useState('');
  const [editMode, setEditMode] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editError, setEditError] = useState('');
  const [saving, setSaving] = useState(false);

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
          setEditTitle(detailsRes.data.data.quiz.title);
          setEditDescription(detailsRes.data.data.quiz.description || '');
          if (detailsRes.data.data.user_progress) {
            setMasteryLevel(detailsRes.data.data.user_progress.mastery_level || 'Not Started');
          }
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

    const saveEdits = async () => {
    try {
      setSaving(true);
      setEditError('');
      const response = await axios.patch(`/api/quizzes/${id}/update-description/`, {
        title: editTitle,
        description: editDescription,
      });
      if (response.data.success) {
        setQuiz(prev => ({ ...prev, title: response.data.data.title, description: response.data.data.description }));
        setEditMode(false);
      } else {
        setEditError(response.data.error || 'Failed to update quiz');
      }
    } catch (err) {
      setEditError(err.response?.data?.error || 'Failed to update quiz');
    } finally {
      setSaving(false);
    }
  };

  const cancelEdits = () => {
    setEditTitle(quiz.title);
    setEditDescription(quiz.description || '');
    setEditError('');
    setEditMode(false);
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
      {editMode ? (
        <div className="card" style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              placeholder="Title"
            />
            <textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              placeholder="Description"
            />
            {editError && <p className="error-message">{editError}</p>}
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button onClick={saveEdits} disabled={saving} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <Check size={16} /> Save
              </button>
              <button onClick={cancelEdits} className="btn" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <X size={16} /> Cancel
              </button>
            </div>
          </div>
        </div>
      ) : (
        <>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {quiz?.title}
            <button onClick={() => setEditMode(true)} className="btn" style={{ padding: '0.25rem' }} title="Edit quiz">
              <Edit2 size={16} />
            </button>
          </h1>
          <p style={{ color: '#7f8c8d', marginBottom: '2rem' }}>{quiz?.description}</p>
        </>
      )}

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

        <div className="card" style={{ textAlign: 'center' }}>
          <TrendingUp size={32} style={{ color: '#9b59b6', marginBottom: '0.5rem' }} />
          <h3 style={{ margin: '0.5rem 0' }}>{masteryLevel}</h3>
          <p style={{ color: '#7f8c8d', margin: 0 }}>Mastery Level</p>
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
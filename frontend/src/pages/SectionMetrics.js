import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import axios from 'axios';
import { ArrowLeft, BarChart3 } from 'lucide-react';

axios.defaults.baseURL = 'https://api.quizcanvas.xyz';

const SectionMetrics = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    const fetchStats = async () => {
      try {
        setLoading(true);
        const res = await axios.get(`/api/quizzes/${id}/statistics/`);
        if (res.data.success) {
          setStats(res.data.data);
        } else {
          setError('Failed to load section metrics');
        }
      } catch (err) {
        setError('Failed to load section metrics');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, [id, isAuthenticated, authLoading, navigate]);

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

  const { quiz, section_stats } = stats || {};

  return (
    <div className="page">
      <div style={{ marginBottom: '1rem' }}>
        <Link to={`/quiz/${id}`} className="btn" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
          <ArrowLeft size={16} /> Back
        </Link>
      </div>
      <h1>{quiz?.title} - Section Metrics</h1>
      {section_stats && section_stats.length > 0 ? (
        <div className="card">
          {section_stats.map((section) => (
            <div key={section.section_id} style={{ marginBottom: '1rem', display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <strong>{section.name}</strong>
                <div style={{ color: '#7f8c8d' }}>{section.question_count} questions</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <BarChart3 size={16} />
                <span>{section.accuracy}% accuracy</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p>No sections available.</p>
      )}
    </div>
  );
};

export default SectionMetrics;

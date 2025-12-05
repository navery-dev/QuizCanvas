import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { CheckCircle, XCircle, Clock, Home, ArrowLeft } from 'lucide-react';
import axios from 'axios';

axios.defaults.baseURL = 'https://api.quizcanvas.xyz';

const ReviewAnswers = () => {
  const { attemptId } = useParams(); // Get attempt ID from URL
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [attemptData, setAttemptData] = useState(null);

  useEffect(() => {
    const fetchAttemptDetails = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`/api/attempts/${attemptId}/details/`);
        
        if (response.data.success) {
          setAttemptData(response.data.data);
        } else {
          setError(response.data.error || 'Failed to load attempt details');
        }
      } catch (err) {
        console.error('Error fetching attempt details:', err);
        setError(err.response?.data?.error || 'Failed to load quiz attempt');
      } finally {
        setLoading(false);
      }
    };

    fetchAttemptDetails();
  }, [attemptId]);

  if (loading) {
    return (
      <div className="page">
        <div className="loading" style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="spinner"></div>
          <p>Loading quiz review...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="error-message">{error}</div>
        <button onClick={() => navigate('/dashboard')} className="btn btn-primary">
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (!attemptData) {
    return null;
  }

  const { attempt, statistics, answers } = attemptData;

  return (
    <div className="page">
      {/* Header Section */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1>Quiz Review: {attempt.quiz_title}</h1>
          <p style={{ color: '#7f8c8d' }}>
            Completed on {new Date(attempt.end_time).toLocaleDateString()}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button 
            onClick={() => navigate(-1)} 
            className="btn btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <ArrowLeft size={16} /> Back
          </button>
          <Link to="/dashboard" className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Home size={16} /> Dashboard
          </Link>
        </div>
      </div>

        {/* Statistics Summary */}
        <div className="card" style={{ marginBottom: '2rem', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <h2 style={{ color: 'white', marginBottom: '1.5rem' }}>Performance Summary</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
            <div style={{ textAlign: 'center' }}>
            <h3 style={{ fontSize: '2.5rem', margin: '0 0 0.5rem 0', color: 'white' }}>
                {Number(attempt.score || 0).toFixed(1)}%
            </h3>
            <p style={{ margin: 0, opacity: 0.9 }}>Final Score</p>
            </div>
            <div style={{ textAlign: 'center' }}>
            <h3 style={{ fontSize: '2.5rem', margin: '0 0 0.5rem 0', color: '#4ade80' }}>
                {statistics.correct_answers || 0}
            </h3>
            <p style={{ margin: 0, opacity: 0.9 }}>Correct</p>
            </div>
            <div style={{ textAlign: 'center' }}>
            <h3 style={{ fontSize: '2.5rem', margin: '0 0 0.5rem 0', color: '#f87171' }}>
                {statistics.incorrect_answers || 0}
            </h3>
            <p style={{ margin: 0, opacity: 0.9 }}>Incorrect</p>
            </div>
            <div style={{ textAlign: 'center' }}>
            <h3 style={{ fontSize: '2.5rem', margin: '0 0 0.5rem 0', color: 'white' }}>
                {attempt.total_time || 'N/A'}
            </h3>
            <p style={{ margin: 0, opacity: 0.9 }}>Time Taken</p>
            </div>
        </div>
        </div>

      {/* Question Review */}
      <h2 style={{ marginBottom: '1rem' }}>Question by Question Review</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {answers.map((answer, index) => (
          <div 
            key={answer.question_id} 
            className="card"
            style={{
              borderLeft: `4px solid ${answer.is_correct ? '#27ae60' : '#e74c3c'}`,
              backgroundColor: answer.is_correct ? '#f0fdf4' : '#fef2f2'
            }}
          >
            {/* Question Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  {answer.is_correct ? (
                    <CheckCircle size={24} style={{ color: '#27ae60' }} />
                  ) : (
                    <XCircle size={24} style={{ color: '#e74c3c' }} />
                  )}
                  <h3 style={{ margin: 0, color: '#2c3e50' }}>
                    Question {index + 1} {answer.is_correct ? '- Correct' : '- Incorrect'}
                  </h3>
                </div>
                <p style={{ color: '#7f8c8d', fontSize: '0.9rem', margin: 0 }}>
                  Section: {answer.section}
                </p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#7f8c8d' }}>
                <Clock size={16} />
                <span>{(answer.response_time / 1000).toFixed(1)}s</span>
              </div>
            </div>

            {/* Question Text */}
            <div style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: 'white', borderRadius: '4px' }}>
              <p style={{ fontSize: '1.1rem', fontWeight: '500', margin: 0 }}>
                {answer.question_text}
              </p>
            </div>

            {/* Answer Options */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {answer.options.map((option, optionIndex) => {
                const isCorrect = optionIndex === answer.correct_answer_index;
                const isSelected = optionIndex === answer.selected_answer_index;
                
                let backgroundColor = 'white';
                let borderColor = '#e0e0e0';
                let textColor = '#2c3e50';
                
                if (isCorrect) {
                  backgroundColor = '#dcfce7';
                  borderColor = '#27ae60';
                  textColor = '#166534';
                } else if (isSelected && !isCorrect) {
                  backgroundColor = '#fee2e2';
                  borderColor = '#e74c3c';
                  textColor = '#991b1b';
                }

                return (
                  <div
                    key={optionIndex}
                    style={{
                      padding: '0.75rem 1rem',
                      backgroundColor,
                      border: `2px solid ${borderColor}`,
                      borderRadius: '4px',
                      color: textColor,
                      fontWeight: (isCorrect || isSelected) ? '600' : '400',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.5rem'
                    }}
                  >
                    <span style={{ 
                      minWidth: '24px', 
                      height: '24px', 
                      borderRadius: '50%', 
                      backgroundColor: borderColor,
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '0.85rem',
                      fontWeight: 'bold'
                    }}>
                      {String.fromCharCode(65 + optionIndex)}
                    </span>
                    <span>{option}</span>
                    {isCorrect && <CheckCircle size={18} style={{ marginLeft: 'auto', color: '#27ae60' }} />}
                    {isSelected && !isCorrect && <XCircle size={18} style={{ marginLeft: 'auto', color: '#e74c3c' }} />}
                  </div>
                );
              })}
            </div>

            {/* Explanation Section (optional - you can add this later) */}
            {!answer.is_correct && (
              <div style={{ 
                marginTop: '1rem', 
                padding: '1rem', 
                backgroundColor: '#fef3c7', 
                borderRadius: '4px',
                border: '1px solid #fbbf24'
              }}>
                <p style={{ margin: 0, color: '#92400e', fontSize: '0.95rem' }}>
                  <strong>Correct Answer:</strong> {answer.correct_answer_text}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Bottom Navigation */}
      <div style={{ marginTop: '2rem', textAlign: 'center' }}>
        <Link to="/dashboard" className="btn btn-primary">
          Return to Dashboard
        </Link>
      </div>
    </div>
  );
};

export default ReviewAnswers;
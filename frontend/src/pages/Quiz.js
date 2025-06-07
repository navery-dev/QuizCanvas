import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import { ArrowLeft, ArrowRight, CheckCircle, Clock } from 'lucide-react';
import axios from 'axios';

const Quiz = () => {
  const { id } = useParams();
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  
  const [quiz, setQuiz] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [attemptId, setAttemptId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [timeLeft, setTimeLeft] = useState(null);
  const [quizCompleted, setQuizCompleted] = useState(false);
  const [results, setResults] = useState(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    const fetchQuizData = async () => {
      try {
        setLoading(true);
        
        // Fetch quiz details
        const quizResponse = await axios.get(`/quizzes/${id}/`);
        setQuiz(quizResponse.data);
        
        // Fetch questions
        const questionsResponse = await axios.get(`/quizzes/${id}/questions/`);
        setQuestions(questionsResponse.data);
        
        // Start quiz attempt
        const attemptResponse = await axios.post(`/quizzes/${id}/start-attempt/`);
        setAttemptId(attemptResponse.data.attempt_id);
        
        // Set timer if quiz has time limit
        if (quizResponse.data.time_limit) {
          setTimeLeft(quizResponse.data.time_limit * 60); // Convert minutes to seconds
        }
        
      } catch (error) {
        console.error('Failed to fetch quiz data:', error);
        setError('Failed to load quiz');
      } finally {
        setLoading(false);
      }
    };
    
    fetchQuizData();
  }, [id, isAuthenticated, navigate]);

  const handleSubmitQuiz = async () => {
    setSubmitting(true);
    try {
      const response = await axios.post(`/quiz-attempts/${attemptId}/submit/`, {
        answers: answers
      });
      
      setResults(response.data);
      setQuizCompleted(true);
      
    } catch (error) {
      console.error('Failed to submit quiz:', error);
      setError('Failed to submit quiz');
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    let interval = null;
    if (timeLeft > 0 && !quizCompleted) {
      interval = setInterval(() => {
        setTimeLeft(timeLeft - 1);
      }, 1000);
    } else if (timeLeft === 0) {
      handleSubmitQuiz();
    }
    return () => clearInterval(interval);
  }, [timeLeft, quizCompleted]);

  const handleAnswerChange = (questionId, selectedOption) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: selectedOption
    }));
  };

  const handleNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    }
  };

  const handlePreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
    }
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getProgressPercentage = () => {
    return ((currentQuestionIndex + 1) / questions.length) * 100;
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

  if (error) {
    return (
      <div className="page">
        <div className="error-message">
          {error}
        </div>
        <button onClick={() => navigate('/dashboard')} className="btn btn-primary">
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (quizCompleted && results) {
    return (
      <div className="page">
        <div className="quiz-container">
          <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
            <CheckCircle size={64} style={{ color: '#27ae60', marginBottom: '2rem' }} />
            <h1 style={{ marginBottom: '1rem' }}>Quiz Completed!</h1>
            <h2 style={{ color: '#3498db', marginBottom: '2rem' }}>
              Your Score: {results.score}%
            </h2>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
              <div>
                <h3 style={{ color: '#27ae60', margin: '0.5rem 0' }}>{results.correct_answers}</h3>
                <p style={{ color: '#7f8c8d', margin: 0 }}>Correct</p>
              </div>
              <div>
                <h3 style={{ color: '#e74c3c', margin: '0.5rem 0' }}>{results.incorrect_answers}</h3>
                <p style={{ color: '#7f8c8d', margin: 0 }}>Incorrect</p>
              </div>
              <div>
                <h3 style={{ color: '#f39c12', margin: '0.5rem 0' }}>{results.total_questions}</h3>
                <p style={{ color: '#7f8c8d', margin: 0 }}>Total Questions</p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
              <button 
                onClick={() => navigate('/dashboard')} 
                className="btn btn-primary"
              >
                Back to Dashboard
              </button>
              <button 
                onClick={() => window.location.reload()} 
                className="btn btn-secondary"
              >
                Retake Quiz
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!quiz || questions.length === 0) {
    return (
      <div className="page">
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <h2>No questions found</h2>
          <p style={{ color: '#7f8c8d', marginBottom: '2rem' }}>
            This quiz doesn't have any questions yet.
          </p>
          <button onClick={() => navigate('/dashboard')} className="btn btn-primary">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];

  return (
    <div className="page">
      <div className="quiz-container">
        {/* Quiz Header */}
        <div style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h1>{quiz.title}</h1>
            {timeLeft !== null && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Clock size={20} />
                <span style={{ 
                  fontWeight: 'bold', 
                  color: timeLeft < 300 ? '#e74c3c' : '#3498db' 
                }}>
                  {formatTime(timeLeft)}
                </span>
              </div>
            )}
          </div>
          
          {/* Progress Bar */}
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${getProgressPercentage()}%` }}
            ></div>
          </div>
          <p style={{ textAlign: 'center', color: '#7f8c8d', marginTop: '0.5rem' }}>
            Question {currentQuestionIndex + 1} of {questions.length}
          </p>
        </div>

        {/* Question Card */}
        <div className="question-card">
          <div className="question-number">
            Question {currentQuestionIndex + 1}
          </div>
          
          <div className="question-text">
            {currentQuestion.question_text}
          </div>

          <ul className="answer-options">
            {currentQuestion.answer_options.map((option, index) => (
              <li key={index} className="answer-option">
                <label>
                  <input
                    type="radio"
                    name={`question_${currentQuestion.id}`}
                    value={index}
                    checked={answers[currentQuestion.id] === index}
                    onChange={() => handleAnswerChange(currentQuestion.id, index)}
                  />
                  {option}
                </label>
              </li>
            ))}
          </ul>

          {/* Navigation */}
          <div className="quiz-navigation">
            <button
              onClick={handlePreviousQuestion}
              disabled={currentQuestionIndex === 0}
              className="btn btn-secondary"
              style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem',
                opacity: currentQuestionIndex === 0 ? 0.5 : 1 
              }}
            >
              <ArrowLeft size={16} />
              Previous
            </button>

            {currentQuestionIndex === questions.length - 1 ? (
              <button
                onClick={handleSubmitQuiz}
                disabled={submitting}
                className="btn btn-primary"
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                <CheckCircle size={16} />
                {submitting ? 'Submitting...' : 'Submit Quiz'}
              </button>
            ) : (
              <button
                onClick={handleNextQuestion}
                className="btn btn-primary"
                style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
              >
                Next
                <ArrowRight size={16} />
              </button>
            )}
          </div>
        </div>

        {/* Question Overview */}
        <div className="card" style={{ marginTop: '2rem' }}>
          <h3 style={{ marginBottom: '1rem' }}>Question Overview</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(40px, 1fr))', gap: '0.5rem' }}>
            {questions.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentQuestionIndex(index)}
                style={{
                  padding: '0.5rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  backgroundColor: 
                    index === currentQuestionIndex ? '#3498db' : 
                    answers[questions[index].id] !== undefined ? '#27ae60' : 
                    'white',
                  color: 
                    index === currentQuestionIndex ? 'white' : 
                    answers[questions[index].id] !== undefined ? 'white' : 
                    '#333',
                  cursor: 'pointer',
                  fontSize: '0.9rem'
                }}
              >
                {index + 1}
              </button>
            ))}
          </div>
          <p style={{ color: '#7f8c8d', fontSize: '0.9rem', marginTop: '1rem' }}>
            <span style={{ color: '#3498db' }}>■</span> Current question • 
            <span style={{ color: '#27ae60' }}> ■</span> Answered • 
            <span style={{ color: '#95a5a6' }}> ■</span> Not answered
          </p>
        </div>
      </div>
    </div>
  );
};

export default Quiz;
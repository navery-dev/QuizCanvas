import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import { ArrowLeft, ArrowRight, CheckCircle, Clock } from 'lucide-react';
import axios from 'axios';

const Quiz = () => {
  const { id } = useParams();
  const { isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
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

  const submitQuiz = useCallback(async () => {
    setSubmitting(true);
    try {
      const response = await axios.post(`/api/attempts/${attemptId}/end/`);
      setResults(response.data.data);
      setQuizCompleted(true);
    } catch (error) {
      console.error('Failed to submit quiz:', error);
      setError('Failed to submit quiz');
    } finally {
      setSubmitting(false);
    }
  }, [attemptId]);

  useEffect(() => {
    if (authLoading) return;
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    const fetchQuizData = async () => {
      let quizData;
      try {
        setLoading(true);

        // Fetch quiz details
        const quizResponse = await axios.get(`/api/quizzes/${id}/`);
        quizData = quizResponse.data.data.quiz;
        setQuiz(quizData);

        // Extract questions from quiz sections
        const allQuestions = [];
        if (quizData.sections) {
          quizData.sections.forEach(section => {
            section.questions.forEach(question => {
              allQuestions.push({
                ...question,
                section_name: section.name
              });
            });
          });
        }
        setQuestions(allQuestions);

        // Start a new attempt
        const attemptResponse = await axios.post(`/api/quizzes/${id}/start/`);
        setAttemptId(attemptResponse.data.data.attempt_id);

        // Set timer for this attempt
        const params = new URLSearchParams(location.search);
        const customTimer = parseInt(params.get('timer'), 10);

        if (!isNaN(customTimer) && customTimer > 0) {
          setTimeLeft(customTimer * 60);
        } else if (quizData.time_limit) {
          setTimeLeft(quizData.time_limit * 60);
        }

      } catch (error) {
        // If an attempt already exists, resume it
        if (error.response && error.response.status === 409) {
          try {
            const existingId = error.response.data.data.attempt_id;
            await axios.post(`/api/attempts/${existingId}/end/`);
            const startRes = await axios.post(`/api/quizzes/${id}/start/`);
            setAttemptId(startRes.data.data.attempt_id);

            // Set timer for resumed/restarted attempt
            const params = new URLSearchParams(location.search);
            const customTimer = parseInt(params.get('timer'), 10);

            if (!isNaN(customTimer) && customTimer > 0) {
              setTimeLeft(customTimer * 60);
            } else if (quizData && quizData.time_limit) {
              setTimeLeft(quizData.time_limit * 60);
            }
          } catch (handleErr) {
            console.error('Failed to handle existing attempt:', handleErr);
            setError('Failed to load quiz');
          }
        } else {
          console.error('Failed to fetch quiz data:', error);
          setError('Failed to load quiz');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchQuizData();
  }, [id, isAuthenticated, authLoading, navigate, location.search]);

  useEffect(() => {
    if (timeLeft > 0 && !quizCompleted) {
      const timer = setInterval(() => {
        setTimeLeft(prev => {
          const newTime = prev - 1;
          if (newTime === 0) {
            clearInterval(timer);
            submitQuiz();
          }
          return newTime;
        });
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [timeLeft, quizCompleted, submitQuiz]);

  const handleAnswerChange = async (questionId, selectedOption) => {
    // Update local state
    setAnswers(prev => ({
      ...prev,
      [questionId]: selectedOption
    }));

    // Submit answer to backend immediately
    try {
      await axios.post(`/api/attempts/${attemptId}/answer/${questionId}/`, {
        selected_option: selectedOption,
        response_time: 5000
      });
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
  };

  const goToPrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(idx => idx - 1);
    }
  };

  const goToNext = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(idx => idx + 1);
    }
  };

  if (loading || authLoading) {
    return <p>Loading quiz...</p>;
  }

  if (error) {
    return <p>{error}</p>;
  }

  if (quizCompleted) {
    return (
      <div className="results">
        <h2>Quiz Results</h2>
        {/* render results */}
      </div>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const minutes = timeLeft != null ? Math.floor(timeLeft / 60) : 0;
  const seconds = timeLeft != null ? timeLeft % 60 : 0;

  return (
    <div className="quiz-page">
      <div className="quiz-header">
        <h1>{quiz.title}</h1>
        {timeLeft != null && (
          <div className="timer">
            <Clock size={20} /> {minutes}:{seconds < 10 ? `0${seconds}` : seconds}
          </div>
        )}
      </div>
      <div className="quiz-content">
        <h2>
          {currentQuestion.section_name}: Question {currentQuestionIndex + 1} of {questions.length}
        </h2>
        <p>{currentQuestion.text}</p>
        <div className="options">
          {['a', 'b', 'c', 'd'].map(optKey => (
            <button
              key={optKey}
              className={`option-btn ${answers[currentQuestion.id] === optKey ? 'selected' : ''}`}
              onClick={() => handleAnswerChange(currentQuestion.id, optKey)}
            >
              {currentQuestion[`option_${optKey}`]}
            </button>
          ))}
        </div>
        <div className="navigation">
          <button onClick={goToPrevious} disabled={currentQuestionIndex === 0}>
            <ArrowLeft /> Previous
          </button>
          <button onClick={goToNext} disabled={currentQuestionIndex === questions.length - 1}>
            Next <ArrowRight />
          </button>
          <button onClick={submitQuiz} disabled={submitting} className="submit-btn">
            <CheckCircle /> Submit Quiz
          </button>
        </div>
        <p className="progress-indicator">
          <span className="current-dot" /> Current question •{' '}
          <span className="answered-dot" /> Answered •{' '}
          <span className="unanswered-dot" /> Not answered
        </p>
      </div>
    </div>
  );
};

export default Quiz;
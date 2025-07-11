import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import { BookOpen, Clock, BarChart3, PlayCircle, TrendingUp, Edit2, Edit3, X, Check } from 'lucide-react';
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
  const [timerMinutes, setTimerMinutes] = useState('none');
  const [editMode, setEditMode] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editError, setEditError] = useState('');
  const [saving, setSaving] = useState(false);
  const [sections, setSections] = useState([]);
  const [editingSection, setEditingSection] = useState(null);
  const [sName, setSName] = useState('');
  const [sDesc, setSDesc] = useState('');
  const [sSaving, setSSaving] = useState(false);
  const [sError, setSError] = useState('');  
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [qText, setQText] = useState('');
  const [qOptions, setQOptions] = useState('');
  const [qAnswer, setQAnswer] = useState('');
  const [qSaving, setQSaving] = useState(false);
  const [qError, setQError] = useState('');
  const [questionEditVisibility, setQuestionEditVisibility] = useState({});

  const hasSections = sections.length > 0;


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
          const qData = detailsRes.data.data.quiz;
          setQuiz(qData);
          setEditTitle(qData.title);
          setEditDescription(qData.description || '');
          setSections(qData.sections || []);

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

  const startQuiz = (sectionId = null) => {
    let url = `/quiz/${id}/take`;
    const params = [];
    if (timerMinutes && timerMinutes !== 'none') {
      params.push(`timer=${timerMinutes}`);
    }
    if (sectionId) {
      params.push(`section=${sectionId}`);
    }
    if (params.length > 0) {
      url += `?${params.join('&')}`;
    }
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

  const startEditSection = (section) => {
    setEditingSection(section);
    setSName(section.name);
    setSDesc(section.description || '');
    setSError('');
  };

  const saveSectionEdits = async () => {
    try {
      if (!editingSection) return;
      setSSaving(true);
      setSError('');
      const payload = {
        name: sName,
        description: sDesc
      };
      const res = await axios.patch(`/api/quizzes/${id}/sections/${editingSection.section_id}/update/`, payload);
      if (res.data.success) {
        setSections((prev) => prev.map((sec) =>
          sec.section_id === editingSection.section_id ? { ...sec, name: res.data.data.name, description: res.data.data.description } : sec
        ));
        setEditingSection(null);
      } else {
        setSError(res.data.error || 'Failed to update section');
      }
    } catch (err) {
      setSError(err.response?.data?.error || 'Failed to update section');
    } finally {
      setSSaving(false);
    }
  };

  const cancelSectionEdits = () => {
    setEditingSection(null);
    setSError('');
  };

  const startEditQuestion = (q) => {
    setEditingQuestion(q);
    setQText(q.text);
    setQOptions(q.options.join(', '));
    setQAnswer(q.answer_index);
    setQError('');
  };

  const saveQuestionEdits = async () => {
    try {
      setQSaving(true);
      setQError('');
      const payload = {
        questionText: qText,
        answerOptions: qOptions.split(',').map((s) => s.trim()).filter((s) => s),
        answerIndex: parseInt(qAnswer, 10)
      };
      const res = await axios.patch(`/api/quizzes/${id}/questions/${editingQuestion.question_id}/update/`, payload);
        if (res.data.success) {
          setSections((prev) => prev.map((sec) =>
            sec.section_id === editingQuestion.section_id ? {
              ...sec,
              questions: sec.questions.map((qu) =>
                qu.question_id === editingQuestion.question_id ? { ...qu, text: res.data.data.questionText, options: res.data.data.answerOptions, answer_index: res.data.data.answerIndex } : qu
              )
            } : sec
        ));
        setEditingQuestion(null);
      } else {
        setQError(res.data.error || 'Failed to update question');
      }
    } catch (err) {
      setQError(err.response?.data?.error || 'Failed to update question');
    } finally {
      setQSaving(false);
    }
  };

  const toggleQuestionEditVisibility = (sectionId) => {
    setQuestionEditVisibility(prev => ({
      ...prev,
      [sectionId]: !prev[sectionId]
    }));
    setEditingQuestion(null);
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
          <label htmlFor="timer" style={{ marginRight: '0.5rem' }}>Timer:</label>
          <select
            id="timer"
            value={timerMinutes}
            onChange={(e) => {
              if (e.target.value === 'custom') {
                const val = window.prompt('Enter timer in minutes');
                if (val && !isNaN(val)) {
                  setTimerMinutes(String(parseInt(val, 10)));
                } else {
                  setTimerMinutes('none');
                }
              } else {
                setTimerMinutes(e.target.value);
              }
            }}
          >
            <option value="none">None</option>
            <option value="1">1</option>
            <option value="15">15</option>
            <option value="30">30</option>
            <option value="60">60</option>
            <option value="custom">Custom...</option>
            {!["none", "1", "15", "30", "60", "custom"].includes(String(timerMinutes)) && (
              <option value={timerMinutes} hidden>
                Custom ({timerMinutes} min)
              </option>
            )}
          </select>
        </div>
        <button onClick={startQuiz} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}>
          <PlayCircle size={16} />
          Start Quiz
        </button>
      </div>
      <div className="card" style={{ marginTop: '2rem' }}>
        <h3 style={{ marginTop: 0 }}>Sections</h3>
        {hasSections && (
          <div style={{ textAlign: 'right', marginBottom: '1rem' }}>
            <Link to={`/quiz/${id}/metrics`} className="btn btn-secondary btn-small">
              View Section Metrics
            </Link>
          </div>
        )}
        {sections.map((section) => {
          const sectionInfo = stats?.section_stats?.find((s) => s.section_id === section.section_id);
          return (
          <div key={section.section_id} style={{ marginBottom: '2rem' }}>
            {editingSection && editingSection.section_id === section.section_id ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <input
                  type="text"
                  value={sName}
                  onChange={(e) => setSName(e.target.value)}
                  placeholder="Section name"
                />
                <textarea
                  value={sDesc}
                  onChange={(e) => setSDesc(e.target.value)}
                  placeholder="Section description"
                />
                {sError && <p className="error-message">{sError}</p>}
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <button onClick={saveSectionEdits} disabled={sSaving} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>                    <Check size={16} /> Save
                  </button>
                  <button onClick={cancelSectionEdits} className="btn" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <X size={16} /> Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div
                className="edit-container"
                style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                    <h4 style={{ margin: '0 0 0.25rem 0' }}>{section.name}</h4>
                    {sectionInfo && (
                      <span className="section-metrics-container">
                        <BarChart3 size={16} style={{ color: '#3498db', cursor: 'pointer' }} />
                        <span className="section-metrics-tooltip">
                          {sectionInfo.question_count} questions
                          <br />
                          Accuracy: {sectionInfo.accuracy}%
                        </span>
                      </span>
                    )}
                  </div>
                  <p style={{ color: '#7f8c8d', margin: 0 }}>{section.description}</p>
                </div>
                <div style={{ display: 'flex', gap: '0.25rem' }}>
                  <button
                    onClick={() => startQuiz(section.section_id)}
                    className="btn btn-primary"
                    style={{ padding: '0.25rem' }}
                    title="Take section quiz"
                  >
                    <PlayCircle size={16} />
                  </button>
                  <button
                    onClick={() => startEditSection(section)}
                    className="btn edit-control"
                    style={{ padding: '0.25rem' }}
                    title="Edit section"
                  >
                    <Edit2 size={16} />
                  </button>
                  {hasSections && (
                    <button
                      onClick={() => toggleQuestionEditVisibility(section.section_id)}
                      className="btn edit-control"
                      style={{ padding: '0.25rem' }}
                      title="Edit questions"
                    >
                      <Edit3 size={16} />
                    </button>
                  )}
                </div>
              </div>
            )}
            <div style={{ marginTop: '1rem', paddingLeft: '1rem' }}>
              {section.questions.map((q) => (
                <div key={q.question_id} style={{ marginBottom: '1rem' }} className="edit-container">
                  {editingQuestion && editingQuestion.question_id === q.question_id ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      <div className="form-group">
                        <label htmlFor="qText">Question</label>
                        <input
                          id="qText"
                          type="text"
                          value={qText}
                          onChange={(e) => setQText(e.target.value)}
                        />
                      </div>
                      <div className="form-group">
                        <label htmlFor="qOptions">Options</label>
                        <input
                          id="qOptions"
                          type="text"
                          value={qOptions}
                          onChange={(e) => setQOptions(e.target.value)}
                          placeholder="Options comma separated"
                        />
                      </div>
                      <div className="form-group">
                        <label htmlFor="qAnswer">Answer Index</label>
                        <input
                          id="qAnswer"
                          type="number"
                          value={qAnswer}
                          onChange={(e) => setQAnswer(e.target.value)}
                        />
                      </div>
                      {qError && <p className="error-message">{qError}</p>}
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button onClick={saveQuestionEdits} disabled={qSaving} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <Check size={16} /> Save
                        </button>
                        <button onClick={() => setEditingQuestion(null)} className="btn" style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                          <X size={16} /> Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem' }}>
                      <span>{q.text}</span>
                      {(!hasSections || questionEditVisibility[section.section_id]) && (
                        <button
                          onClick={() => startEditQuestion({ ...q, section_id: section.section_id })}
                          className="btn edit-control"
                          style={{ padding: '0.25rem' }}
                          title="Edit question"
                        >
                          <Edit2 size={16} />
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
        })}
      </div>
    </div>
  );
};

export default QuizLanding;
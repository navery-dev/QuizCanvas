import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import { Upload as UploadIcon, AlertCircle, CheckCircle } from 'lucide-react';
import axios from 'axios';

const Upload = () => {
  const { isAuthenticated } = useAuth();
  const [file, setFile] = useState(null);
  const [quizTitle, setQuizTitle] = useState('');
  const [quizDescription, setQuizDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  React.useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, navigate]);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
    setError('');
    setSuccess('');
    
    // Auto-generate title from filename if no title is set
    if (selectedFile && !quizTitle) {
      const nameWithoutExtension = selectedFile.name.replace(/\.[^/.]+$/, "");
      setQuizTitle(nameWithoutExtension.replace(/[-_]/g, ' '));
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setError('');
      setSuccess('');
      
      if (!quizTitle) {
        const nameWithoutExtension = droppedFile.name.replace(/\.[^/.]+$/, "");
        setQuizTitle(nameWithoutExtension.replace(/[-_]/g, ' '));
      }
    }
  };

  const validateFile = () => {
    if (!file) {
      setError('Please select a file to upload');
      return false;
    }

    const allowedTypes = ['text/csv', 'application/json'];
    const fileExtension = file.name.toLowerCase().split('.').pop();
    
    if (!allowedTypes.includes(file.type) && !['csv', 'json'].includes(fileExtension)) {
      setError('Please upload a CSV or JSON file');
      return false;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      setError('File size must be less than 10MB');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateFile()) {
      return;
    }

    if (!quizTitle.trim()) {
      setError('Please enter a quiz title');
      return;
    }

    setUploading(true);
    setError('');
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('title', quizTitle.trim());
      formData.append('description', quizDescription.trim());

      await axios.post('/quizzes/upload/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadProgress(progress);
        }
      });

      setSuccess('Quiz uploaded successfully!');
      setFile(null);
      setQuizTitle('');
      setQuizDescription('');
      setUploadProgress(0);
      
      // Redirect to dashboard after a short delay
      setTimeout(() => {
        navigate('/dashboard');
      }, 2000);

    } catch (error) {
      console.error('Upload failed:', error);
      setError(
        error.response?.data?.detail || 
        error.response?.data?.error || 
        'Failed to upload quiz'
      );
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="page">
      <h1>Upload Quiz Content</h1>
      <p style={{ color: '#7f8c8d', marginBottom: '2rem' }}>
        Upload your quiz questions in CSV or JSON format to create a new quiz.
      </p>

      {error && (
        <div className="error-message">
          <AlertCircle size={16} style={{ marginRight: '0.5rem' }} />
          {error}
        </div>
      )}

      {success && (
        <div className="success-message">
          <CheckCircle size={16} style={{ marginRight: '0.5rem' }} />
          {success}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
        {/* Upload Form */}
        <div className="card">
          <h2>Upload File</h2>
          
          <form onSubmit={handleSubmit}>
            {/* File Upload Area */}
            <div 
              style={{
                border: '2px dashed #bdc3c7',
                borderRadius: '8px',
                padding: '2rem',
                textAlign: 'center',
                marginBottom: '1rem',
                backgroundColor: file ? '#e8f5e8' : '#f8f9fa',
                borderColor: file ? '#27ae60' : '#bdc3c7',
                cursor: 'pointer'
              }}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => document.getElementById('fileInput').click()}
            >
              <UploadIcon size={48} style={{ color: file ? '#27ae60' : '#bdc3c7', marginBottom: '1rem' }} />
              {file ? (
                <div>
                  <p style={{ color: '#27ae60', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                    File selected: {file.name}
                  </p>
                  <p style={{ color: '#7f8c8d', fontSize: '0.9rem' }}>
                    Size: {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              ) : (
                <div>
                  <p style={{ marginBottom: '0.5rem' }}>
                    Drag and drop your file here, or click to browse
                  </p>
                  <p style={{ color: '#7f8c8d', fontSize: '0.9rem' }}>
                    Supports CSV and JSON files (max 10MB)
                  </p>
                </div>
              )}
            </div>

            <input
              type="file"
              id="fileInput"
              accept=".csv,.json"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />

            {/* Quiz Details */}
            <div className="form-group">
              <label htmlFor="quizTitle">Quiz Title *</label>
              <input
                type="text"
                id="quizTitle"
                value={quizTitle}
                onChange={(e) => setQuizTitle(e.target.value)}
                placeholder="Enter quiz title"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="quizDescription">Description (Optional)</label>
              <textarea
                id="quizDescription"
                value={quizDescription}
                onChange={(e) => setQuizDescription(e.target.value)}
                placeholder="Enter quiz description"
                rows="3"
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontFamily: 'inherit',
                  fontSize: '1rem',
                  resize: 'vertical'
                }}
              />
            </div>

            {/* Upload Progress */}
            {uploading && (
              <div className="form-group">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                <p style={{ textAlign: 'center', color: '#7f8c8d', fontSize: '0.9rem' }}>
                  Uploading... {uploadProgress}%
                </p>
              </div>
            )}

            <button 
              type="submit" 
              className="btn btn-primary btn-full-width"
              disabled={uploading || !file}
            >
              {uploading ? 'Uploading...' : 'Upload Quiz'}
            </button>
          </form>
        </div>

        {/* Instructions */}
        <div className="card">
          <h2>File Format Requirements</h2>
          
          <div style={{ marginBottom: '2rem' }}>
            <h3 style={{ color: '#3498db', marginBottom: '1rem' }}>CSV Format</h3>
            <p style={{ marginBottom: '1rem', color: '#7f8c8d' }}>
              Your CSV file should have the following columns:
            </p>
            <ul style={{ color: '#7f8c8d', paddingLeft: '1.5rem' }}>
              <li><strong>question</strong> - The question text</li>
              <li><strong>option_a</strong> - First answer option</li>
              <li><strong>option_b</strong> - Second answer option</li>
              <li><strong>option_c</strong> - Third answer option</li>
              <li><strong>option_d</strong> - Fourth answer option</li>
              <li><strong>correct_answer</strong> - The correct option (a, b, c, or d)</li>
              <li><strong>section</strong> - Section name (optional)</li>
            </ul>
          </div>

          <div style={{ marginBottom: '2rem' }}>
            <h3 style={{ color: '#27ae60', marginBottom: '1rem' }}>JSON Format</h3>
            <p style={{ marginBottom: '1rem', color: '#7f8c8d' }}>
              Your JSON file should be an array of question objects:
            </p>
            <div style={{ 
              backgroundColor: '#f8f9fa', 
              padding: '1rem', 
              borderRadius: '4px',
              fontSize: '0.9rem',
              fontFamily: 'monospace',
              border: '1px solid #e9ecef'
            }}>
              {`[
  {
    "question": "What is 2+2?",
    "options": ["3", "4", "5", "6"],
    "correct_answer": 1,
    "section": "Math"
  }
]`}
            </div>
          </div>

          <div style={{ padding: '1rem', backgroundColor: '#fff3cd', borderRadius: '4px', border: '1px solid #ffeaa7' }}>
            <p style={{ margin: 0, color: '#856404', fontSize: '0.9rem' }}>
              <strong>Tip:</strong> Make sure your file is properly formatted and all required fields are included. 
              The system will organize your questions into sections automatically.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Upload;
import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../services/AuthContext';
import { BookOpen, Upload, BarChart3, Users } from 'lucide-react';

const Home = () => {
  const { isAuthenticated } = useAuth();

  return (
    <div className="page">
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <h1 style={{ fontSize: '3rem', marginBottom: '1rem', color: '#2c3e50' }}>
          Welcome to QuizCanvas
        </h1>
        <p style={{ fontSize: '1.2rem', color: '#7f8c8d', maxWidth: '600px', margin: '0 auto' }}>
          Your customizable learning platform for quizzes, exams, and certifications. 
          Upload your own content and track your progress across any subject.
        </p>
      </div>

      <div style={{ textAlign: 'center', background: 'white', padding: '2rem', borderRadius: '8px', boxShadow: '0 2px 10px rgba(0,0,0,0.1)', marginBottom: '3rem' }}>
        <h2 style={{ marginBottom: '1rem', color: '#2c3e50' }}>Ready to Start Learning?</h2>
        {isAuthenticated ? (
          <div>
            <p style={{ marginBottom: '1.5rem', color: '#7f8c8d' }}>
              Welcome back! Continue your learning journey.
            </p>
            <Link to="/dashboard" className="btn btn-primary" style={{ marginRight: '1rem' }}>
              Go to Dashboard
            </Link>
            <Link to="/upload" className="btn btn-secondary">
              Upload New Quiz
            </Link>
          </div>
        ) : (
          <div>
            <p style={{ marginBottom: '1.5rem', color: '#7f8c8d' }}>
              Create an account to start uploading your quiz content and tracking your progress.
            </p>
            <Link to="/register" className="btn btn-primary" style={{ marginRight: '1rem' }}>
              Get Started
            </Link>
            <Link to="/login" className="btn btn-secondary">
              Sign In
            </Link>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '2rem' }}>
        <div className="card" style={{ textAlign: 'center' }}>
          <Upload size={48} style={{ color: '#3498db', margin: '0 auto 1rem' }} />
          <h3>Upload Content</h3>
          <p>Import your quiz questions from CSV or JSON files. Organize content into sections and modules.</p>
        </div>
        
        <div className="card" style={{ textAlign: 'center' }}>
          <BookOpen size={48} style={{ color: '#27ae60', margin: '0 auto 1rem' }} />
          <h3>Take Quizzes</h3>
          <p>Test your knowledge with customizable multiple-choice quizzes. Navigate questions and track time.</p>
        </div>
        
        <div className="card" style={{ textAlign: 'center' }}>
          <BarChart3 size={48} style={{ color: '#e74c3c', margin: '0 auto 1rem' }} />
          <h3>Track Progress</h3>
          <p>Monitor your learning progress with detailed analytics and mastery level indicators.</p>
        </div>
        
        <div className="card" style={{ textAlign: 'center' }}>
          <Users size={48} style={{ color: '#9b59b6', margin: '0 auto 1rem' }} />
          <h3>For Everyone</h3>
          <p>Perfect for students, professionals pursuing certifications, or anyone learning new skills.</p>
        </div>
      </div>
    </div>
  );
};

export default Home;
import React, { useState } from 'react';
import { ChevronDown, ChevronUp, HelpCircle } from 'lucide-react';

const FAQ = () => {
  const [openItems, setOpenItems] = useState({});

  const toggleItem = (index) => {
    setOpenItems(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const faqData = [
    {
      category: "Getting Started",
      questions: [
        {
          question: "What is QuizCanvas?",
          answer: "QuizCanvas is a customizable learning platform that allows you to upload your own quiz content in CSV or JSON format, take quizzes, and track your learning progress across any subject."
        },
        {
          question: "Is QuizCanvas free to use?",
          answer: "Yes! QuizCanvas is completely free to use. There are no subscription fees, per-course charges, or hidden costs. Create an account and start learning today."
        },
        {
          question: "Do I need to install any software?",
          answer: "No installation required! QuizCanvas is a web-based application that runs in your browser. Just visit the website, create an account, and start using it immediately."
        }
      ]
    },
    {
      category: "File Uploads & Quiz Creation",
      questions: [
        {
          question: "What file formats can I upload?",
          answer: "QuizCanvas supports CSV and JSON file formats. Your files should contain quiz questions with multiple-choice answers and the correct answer indicated."
        },
        {
          question: "What's the required format for CSV files?",
          answer: "CSV files should have columns: 'question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer' (a, b, c, or d), and optionally 'section' for organizing questions."
        },
        {
          question: "What's the required format for JSON files?",
          answer: "JSON files should be an array of objects with: 'question' (string), 'options' (array of 4 strings), 'correct_answer' (number 0-3), and optionally 'section' (string)."
        },
        {
          question: "Is there a limit on file size?",
          answer: "Yes, uploaded files must be smaller than 10MB. This typically allows for thousands of questions per file."
        },
        {
          question: "Can I organize questions into sections?",
          answer: "Yes! You can include a 'section' column in your CSV or JSON file. Questions will be organized into these sections in the quiz landing page."
        }
      ]
    },
    {
      category: "Taking Quizzes",
      questions: [
        {
          question: "Can I navigate between questions during a quiz?",
          answer: "Yes! You can move forward and backward between questions, and there's a question overview that shows your progress and allows quick navigation to any question."
        },
        {
          question: "Are quizzes timed?",
          answer: "You can set a timer before starting the quiz if you want. A count down will be displayed and unanswered questions will be counted as incorrect when the timer is complete"
        },
        {
          question: "Can I pause and resume a quiz?",
          answer: "Direct pausing isn't currently available, however, if you accidentally close your browser or navigate away, you can resume your quiz attempt from where you left off (within the time limit if applicable)."
        },
        {
          question: "Can I retake quizzes?",
          answer: "Absolutely! You can retake any quiz as many times as you want. This helps reinforce learning and improve your scores over time."
        }
      ]
    },
    {
      category: "Progress Tracking",
      questions: [
        {
          question: "How does progress tracking work?",
          answer: "QuizCanvas tracks your quiz attempts, scores, improvement over time, and mastery levels for different sections. You can view detailed analytics on your dashboard."
        },
        {
          question: "What is a mastery level?",
          answer: "Mastery levels indicate your proficiency in different topics based on your quiz performance. They help identify areas where you're excelling and areas that need more practice."
        },
        {
          question: "Can I see my quiz history?",
          answer: "Yes! Your dashboard shows recent quiz attempts, scores, and you can view detailed results for each attempt to see which questions you got right or wrong."
        }
      ]
    },
    {
      category: "Account Management",
      questions: [
        {
          question: "How do I create an account?",
          answer: "Click 'Get Started' or 'Register' and fill out the registration form with your username, email, and password. You'll be able to start using QuizCanvas immediately."
        },
        {
          question: "Can I change my account information?",
          answer: "Yes! Go to your Profile page to update your username and email."
        },
        {
          question: "What if I forget my password?",
          answer: "Password resets are not currently available and will be implemented in future development"
        },
        {
          question: "Can I delete my account?",
          answer: "Account deletion options are available in your profile settings. Please note that this will permanently remove all your quizzes and progress data."
        }
      ]
    },
    {
      category: "Technical Support",
      questions: [
        {
          question: "Which browsers are supported?",
          answer: "QuizCanvas works on all modern browsers including Chrome, Firefox, Safari, and Edge. We recommend using the latest version for the best experience."
        },
        {
          question: "What if my file upload fails?",
          answer: "Check that your file is under 10MB and in the correct CSV or JSON format. Make sure all required columns are present and properly formatted."
        },
        {
          question: "Why isn't my quiz loading?",
          answer: "This could be due to an issue with your uploaded file format or a temporary connection issue. Try refreshing the page or re-uploading your file."
        }
      ]
    }
  ];

  return (
    <div className="page">
      <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
        <HelpCircle size={64} style={{ color: '#3498db', marginBottom: '1rem' }} />
        <h1>Frequently Asked Questions</h1>
        <p style={{ color: '#7f8c8d', fontSize: '1.1rem', maxWidth: '600px', margin: '0 auto' }}>
          Find answers to common questions about using QuizCanvas. 
        </p>
      </div>

      {faqData.map((category, categoryIndex) => (
        <div key={categoryIndex} style={{ marginBottom: '2rem' }}>
          <h2 style={{ 
            color: '#2c3e50', 
            marginBottom: '1rem',
            paddingBottom: '0.5rem',
            borderBottom: '2px solid #3498db'
          }}>
            {category.category}
          </h2>
          
          <div style={{ display: 'grid', gap: '0.5rem' }}>
            {category.questions.map((item, questionIndex) => {
              const itemKey = `${categoryIndex}-${questionIndex}`;
              const isOpen = openItems[itemKey];
              
              return (
                <div key={itemKey} className="card" style={{ padding: 0 }}>
                  <button
                    onClick={() => toggleItem(itemKey)}
                    style={{
                      width: '100%',
                      padding: '1.5rem',
                      border: 'none',
                      background: 'none',
                      textAlign: 'left',
                      cursor: 'pointer',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      fontSize: '1.1rem',
                      fontWeight: '500',
                      color: '#2c3e50'
                    }}
                  >
                    <span>{item.question}</span>
                    {isOpen ? (
                      <ChevronUp size={20} style={{ color: '#3498db', flexShrink: 0, marginLeft: '1rem' }} />
                    ) : (
                      <ChevronDown size={20} style={{ color: '#7f8c8d', flexShrink: 0, marginLeft: '1rem' }} />
                    )}
                  </button>
                  
                  {isOpen && (
                    <div style={{ 
                      padding: '0 1.5rem 1.5rem 1.5rem',
                      borderTop: '1px solid #ecf0f1'
                    }}>
                      <p style={{ 
                        margin: 0, 
                        color: '#7f8c8d',
                        lineHeight: '1.6',
                        fontSize: '1rem'
                      }}>
                        {item.answer}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      ))}  
    </div>
  );
};

export default FAQ;
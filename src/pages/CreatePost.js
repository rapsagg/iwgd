import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import '../styles/CreatePost.css';
import { postAPI, topicAPI } from '../services/api';

export default function CreatePost() {
  const navigate = useNavigate();
  const { topicId } = useParams();
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    topic: topicId || '',
    tags: '',
    attachments: []
  });
  const [topics, setTopics] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [charCount, setCharCount] = useState(0);
  const [newTopicName, setNewTopicName] = useState('');
  const MAX_CHARS = 5000;

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (!token) {
      navigate('/');
      return;
    }
    
    // Fetch real topics from API
    const fetchTopics = async () => {
      try {
        const response = await topicAPI.getAllTopics();
        setTopics(response.data.results || response.data);
      } catch (err) {
        console.error('Failed to fetch topics', err);
        setTopics([]);
      }
    };
    
    fetchTopics();
  }, [navigate]);

  const handleContentChange = (e) => {
    const text = e.target.value;
    if (text.length <= MAX_CHARS) {
      setFormData({ ...formData, content: text });
      setCharCount(text.length);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const handleFileAttach = (e) => {
    const files = Array.from(e.target.files);
    setFormData({
      ...formData,
      attachments: [...formData.attachments, ...files]
    });
  };

  const removeAttachment = (index) => {
    setFormData({
      ...formData,
      attachments: formData.attachments.filter((_, i) => i !== index)
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log('Full formData:', formData);  // Add this first
    setError('');
    
    if (!formData.title.trim()) {
      console.log('Error: No title');  // Add this
      setError('Title is required');
      return;
    }
    
    if (!formData.content.trim()) {
      console.log('Error: No content');  // Add this
      setError('Content is required');
      return;
    }
    
    if (!formData.topic && !newTopicName) {
      console.log('Error: No topic');  // Add this
      setError('Please select a topic or create a new one');
      return;
    }

    setLoading(true);
    
    try {
      let topicId = formData.topic;
      
      // If creating new topic, create it first
      if (formData.topic === 'new' && newTopicName.trim()) {
        const topicResponse = await topicAPI.createTopic({ 
          name: newTopicName.trim(),
          description: '' 
        });
        topicId = topicResponse.data.id;
      }
      
      const postData = {
        title: formData.title,
        content: formData.content,
        topic_id: topicId,
        // tags and attachments are optional
        ...(formData.tags && { tags: formData.tags.split(',').map(t => t.trim()).filter(t => t) })
      };

      await postAPI.createPost(postData);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || err.response?.data?.error || 'Failed to create post');
      console.error('Create post error:', err.response?.data);
    } finally {
      setLoading(false);
    }
  };  

  return (
    <div className="create-post-container">
      <div className="create-post-card">
        <h1>Create Post</h1>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="title">Title</label>
            <input
              type="text"
              id="title"
              name="title"
              className="form-control"
              value={formData.title}
              onChange={handleInputChange}
              placeholder="What's on your mind?"
              maxLength="200"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="content">
              Content ({charCount}/{MAX_CHARS})
            </label>
            <textarea
              id="content"
              name="content"
              className="form-control create-post-textarea"
              value={formData.content}
              onChange={handleContentChange}
              placeholder="Share your thoughts..."
              rows="8"
            />
            <div className="char-count-bar">
              <div 
                className="char-count-fill"
                style={{ width: `${(charCount / MAX_CHARS) * 100}%` }}
              ></div>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="topic">Topic</label>
            <select
              id="topic"
              name="topic"
              className="form-control"
              value={formData.topic}
              onChange={handleInputChange}
            >
              <option value="">Select a topic</option>
              {topics.map(t => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
              <option value="new">+ Create new topic</option>
            </select>
          </div>

          {formData.topic === 'new' && (
            <div className="form-group">
              <label className="form-label" htmlFor="newTopic">New Topic Name</label>
              <input
                type="text"
                id="newTopic"
                className="form-control"
                value={newTopicName}
                onChange={(e) => setNewTopicName(e.target.value)}
                placeholder="Enter topic name"
              />
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="tags">Tags (comma-separated)</label>
            <input
              type="text"
              id="tags"
              name="tags"
              className="form-control"
              value={formData.tags}
              onChange={handleInputChange}
              placeholder="e.g. discussion, help, announcement"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Attachments</label>
            <div className="attachment-input-wrapper">
              <input
                type="file"
                id="attachments"
                multiple
                onChange={handleFileAttach}
                className="attachment-input"
                accept="image/*,video/*,.pdf"
              />
              <label htmlFor="attachments" className="attachment-label">
                <span>+ Add images, videos, or files</span>
              </label>
            </div>

            {formData.attachments.length > 0 && (
              <div className="attachments-list">
                {formData.attachments.map((file, index) => (
                  <div key={index} className="attachment-item">
                    <span>{file.name}</span>
                    <button
                      type="button"
                      onClick={() => removeAttachment(index)}
                      className="attachment-remove"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="form-actions">
            <button
              type="button"
              className="btn btn--outline"
              onClick={() => navigate(-1)}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn--primary"
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create Post'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

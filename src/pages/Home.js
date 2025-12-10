import React, { useState, useEffect } from 'react';
import { postAPI, reactionAPI } from '../services/api';
import authService from '../services/auth';
import '../styles/Home.css';
import { useNavigate } from 'react-router-dom';

function Home() {
  const [activeTab, setActiveTab] = useState('popular'); // 'popular' or 'following'
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const isGuest = authService.isGuest();
  const navigate = useNavigate();
  const isLoggedIn = !!localStorage.getItem('authToken');

  useEffect(() => {
    fetchPosts();
  }, [activeTab]);

  const fetchPosts = async () => {
    setLoading(true);
    setError('');
    try {
      let data;
      if (activeTab === 'popular') {
        data = await postAPI.getAllPosts(1, 20, '-likes_count');
      } else {
        data = await postAPI.getAllPosts(1, 20, '-created_at');
      }
      console.log('Posts with is_liked:', data.data.results); // Check this
      setPosts(data.data.results || []);
    } catch (err) {
      setError('Failed to load posts');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async (postId) => {
    if (isGuest) {
      alert('Please login to like posts');
      return;
    }
    
    try {
      const response = await reactionAPI.toggleLike(postId);
      console.log('Like response:', response.data); // Add this
      
      // Update the post in the list
      setPosts(posts.map(post => 
        post.id === postId 
          ? { 
              ...post, 
              is_liked: response.data.liked, 
              likes_count: response.data.likes_count 
            }
          : post
      ));
    } catch (err) {
      console.error('Failed to like post:', err);
      console.error('Error response:', err.response?.data);
      alert('Failed to like post: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleComment = async (postId) => {
    if (isGuest) {
      alert('Please login to comment on posts');
      return;
    }
    navigate(`/post/${postId}`);
  };

  return (
    <div className="home-container">
      <div className="home-header">
        <h1>Politics Forum</h1>
        <p className="subtitle">Discuss politics, share opinions, and earn reputation</p>
      </div>

      {/* Tabs */}
      <div className="home-tabs">
        <button
          className={`tab ${activeTab === 'popular' ? 'active' : ''}`}
          onClick={() => setActiveTab('popular')}
        >
          🔥 Popular
        </button>
        <button
          className={`tab ${activeTab === 'following' ? 'active' : ''}`}
          onClick={() => setActiveTab('following')}
        >
          📌 Following
        </button>
      </div>

      {isLoggedIn && (
        <button
          onClick={() => navigate('/create')}
          className="btn btn--primary"
          style={{ marginBottom: 'var(--space-20)' }}
        >
          + Create Post
        </button>
      )}

      {/* Loading */}
      {loading && <div className="loading">Loading posts...</div>}

      {/* Error */}
      {error && <div className="error-message">{error}</div>}

      {/* Guest mode notice */}
      {isGuest && (
        <div className="guest-notice">
          👤 You are browsing as a guest. <a href="/login">Login or register</a> to interact with posts.
        </div>
      )}

      {/* Posts list */}
      <div className="posts-list">
        {posts.length === 0 && !loading ? (
          <div className="empty-state">
            <p>No posts yet. Be the first to share!</p>
          </div>
        ) : (
          posts.map((post) => (
            <div key={post.id} className="post-card"
              onClick={() => navigate(`/post/${post.id}`)}>
              <div className="post-header">
                <button 
                  className="post-topic-link"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/topic/${post.topic.id}`);
                  }}
                >
                  {post.topic.name}
                </button>
            <div className="post-meta-right">
              <div className="post-author-info">
                    <button 
                      className="author-name-link"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/profile/${post.creator.user_id}`);
                      }}
                    >
                      {post.creator.username}
                    </button>
                {post.creator.reputation_tier && (
                  <span className="author-tier">
                    Tier {post.creator.reputation_tier.tier_number}
                  </span>
                )}
              </div>
              <span className="post-time">
                {new Date(post.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>

              <h3 className="post-title">{post.title}</h3>
              <p className="post-content">
                {post.content.length > 200
                  ? `${post.content.substring(0, 200)}...`
                  : post.content}
              </p>

              <div className="post-actions">
                <button 
                  className={`action-btn ${post.is_liked ? 'liked' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleLike(post.id);
                  }}
                >
                  {post.is_liked ? '👍' : '👍'} {post.likes_count}
                </button>
                <button 
                  className="action-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleComment(post.id);
                  }}
                  style={{ cursor: 'pointer' }}
                >
                  💬 {post.comments_count}
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default Home;

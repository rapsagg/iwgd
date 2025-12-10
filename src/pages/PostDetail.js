import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { postAPI, reactionAPI } from '../services/api';
import authService from '../services/auth';
import Comments from '../components/Comments';
import '../styles/PostDetail.css';

function PostDetail() {
  const { postId } = useParams();
  const navigate = useNavigate();
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const isGuest = authService.isGuest();

  useEffect(() => {
    fetchPost();
  }, [postId]);

  const fetchPost = async () => {
    try {
      const response = await postAPI.getPost(postId);
      setPost(response.data);
    } catch (err) {
      setError('Failed to load post');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async () => {
    if (isGuest) {
      alert('Please login to like posts');
      return;
    }

    try {
      const response = await reactionAPI.toggleLike(postId);
      setPost({
        ...post,
        is_liked: response.data.liked,
        likes_count: response.data.likes_count
      });
    } catch (err) {
      console.error('Failed to like post:', err);
      alert('Failed to like post');
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (error || !post) {
    return (
      <div className="error-container">
        <h2>{error || 'Post not found'}</h2>
        <button onClick={() => navigate('/')}>Go Back Home</button>
      </div>
    );
  }

  return (
    <div className="post-detail-container">
      <button className="back-btn" onClick={() => navigate(-1)}>
        ← Back
      </button>

      <div className="post-detail-card">
        <div className="post-header">
          <div className="post-meta-left">
            {post.topic && (
              <button className="post-topic-link">
                {post.topic.name}
              </button>
            )}
          </div>
          <div className="post-meta-right">
            <div className="post-author-info">
              <button className="author-name-link">
                {post.creator?.username || 'Unknown'}
              </button>
              {post.creator?.reputation_tier && (
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

        <h1 className="post-title">{post.title}</h1>

        <div className="post-content">
          <p>{post.content}</p>
        </div>

        <div className="post-actions">
          <button 
            className={`action-btn ${post.is_liked ? 'liked' : ''}`}
            onClick={handleLike}
          >
            👍 {post.likes_count || 0}
          </button>
          <span className="action-btn">
            💬 {post.comments_count || 0}
          </span>
        </div>
      </div>

      {/* Comments Component */}
      <Comments postId={postId} />
    </div>
  );
}

export default PostDetail;

import React, { useState, useEffect } from 'react';
import { commentAPI } from '../services/api';
import authService from '../services/auth';
import '../styles/PostDetail.css';

function Comments({ postId }) {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(false);
  const [sortBy, setSortBy] = useState('likes'); // 'likes', 'newest', 'oldest'
  const isGuest = authService.isGuest();

  useEffect(() => {
    fetchComments();
  }, [postId]);

  const fetchComments = async () => {
    try {
      const response = await commentAPI.getComments(postId);
      setComments(response.data.results || response.data || []);
    } catch (err) {
      console.error('Failed to load comments:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    if (isGuest) {
      alert('Please login to comment');
      return;
    }

    setLoading(true);
    try {
      await commentAPI.createComment(postId, newComment);
      setNewComment('');
      fetchComments();
    } catch (err) {
      console.error('Failed to post comment:', err);
      alert('Failed to post comment');
    } finally {
      setLoading(false);
    }
  };

  const getSortedComments = () => {
    const sorted = [...comments];
    if (sortBy === 'likes') {
      return sorted.sort((a, b) => (b.likes_count || 0) - (a.likes_count || 0));
    } else if (sortBy === 'newest') {
      return sorted.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    } else if (sortBy === 'oldest') {
      return sorted.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    }
    return sorted;
  };

  const sortedComments = getSortedComments();

  return (
    <div className="comments-section">
      <div className="comments-header">
        <h3>Comments ({comments.length})</h3>
        <div className="sort-buttons">
          <button 
            className={sortBy === 'likes' ? 'active' : ''}
            onClick={() => setSortBy('likes')}
          >
            Top
          </button>
          <button 
            className={sortBy === 'newest' ? 'active' : ''}
            onClick={() => setSortBy('newest')}
          >
            Newest
          </button>
          <button 
            className={sortBy === 'oldest' ? 'active' : ''}
            onClick={() => setSortBy('oldest')}
          >
            Oldest
          </button>
        </div>
      </div>
      
      {!isGuest && (
        <form onSubmit={handleSubmit} className="comment-form">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Write a comment..."
            rows="3"
          />
          <button type="submit" disabled={loading || !newComment.trim()}>
            {loading ? 'Posting...' : 'Post Comment'}
          </button>
        </form>
      )}

      {isGuest && (
        <div className="guest-notice">
          <p>Log in to comment on posts</p>
        </div>
      )}

      <div className="comments-list">
        {sortedComments.length === 0 ? (
          <p className="no-comments">No comments yet. Be the first!</p>
        ) : (
          sortedComments.map((comment) => (
            <div key={comment.id} className="comment">
              <div className="comment-header">
                <strong>{comment.creator?.username || 'Unknown'}</strong>
                <span className="comment-date">
                  {new Date(comment.created_at).toLocaleDateString()}
                </span>
              </div>
              <p className="comment-content">{comment.content}</p>
              <div className="comment-footer">
                <span>👍 {comment.likes_count || 0}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default Comments;

import React, { useState, useEffect } from 'react';
import { getComments, createComment, deleteComment } from '../../api/comments';
import styles from './TaskComments.module.css';

function TaskComments({ taskId }) {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showMentions, setShowMentions] = useState(false);
  const [mentionSearch, setMentionSearch] = useState('');
  const [cursorPosition, setCursorPosition] = useState(0);

  // Mock users for mentions
  const users = [
    { id: 1, name: 'John Doe', avatar: null },
    { id: 2, name: 'Jane Smith', avatar: null },
    { id: 3, name: 'Bob Johnson', avatar: null },
  ];

  useEffect(() => {
    loadComments();
  }, [taskId]);

  const loadComments = async () => {
    try {
      const response = await getComments(taskId);
      setComments(response.data);
    } catch (error) {
      console.error('Failed to load comments:', error);
    }
  };

  const handleCommentChange = (e) => {
    const value = e.target.value;
    const position = e.target.selectionStart;
    
    setNewComment(value);
    setCursorPosition(position);

    // Check for @ mention
    const textBeforeCursor = value.substring(0, position);
    const mentionMatch = textBeforeCursor.match(/@(\w*)$/);
    
    if (mentionMatch) {
      setMentionSearch(mentionMatch[1]);
      setShowMentions(true);
    } else {
      setShowMentions(false);
    }
  };

  const handleMentionSelect = (user) => {
    const textBeforeCursor = newComment.substring(0, cursorPosition);
    const textAfterCursor = newComment.substring(cursorPosition);
    const mentionMatch = textBeforeCursor.match(/(.*)@(\w*)$/);
    
    if (mentionMatch) {
      const newValue = `${mentionMatch[1]}@${user.name} ${textAfterCursor}`;
      setNewComment(newValue);
      setShowMentions(false);
    }
  };

  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(mentionSearch.toLowerCase())
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newComment.trim() || isSubmitting) return;

    try {
      setIsSubmitting(true);
      const response = await createComment({
        taskId,
        text: newComment,
      });
      setComments([response.data, ...comments]);
      setNewComment('');
    } catch (error) {
      console.error('Failed to create comment:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (commentId) => {
    if (window.confirm('Delete this comment?')) {
      try {
        await deleteComment(commentId);
        setComments(comments.filter(c => c.id !== commentId));
      } catch (error) {
        console.error('Failed to delete comment:', error);
      }
    }
  };

  const formatCommentText = (text) => {
    // Highlight mentions
    return text.replace(/@(\w+)/g, '<span class="mention">@$1</span>');
  };

  const formatDate = (date) => {
    const now = new Date();
    const commentDate = new Date(date);
    const diffMs = now - commentDate;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return commentDate.toLocaleDateString();
  };

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Comments ({comments.length})</h2>

      <form onSubmit={handleSubmit} className={styles.commentForm}>
        <div className={styles.inputContainer}>
          <textarea
            className={styles.textarea}
            value={newComment}
            onChange={handleCommentChange}
            placeholder="Write a comment... (Use @ to mention someone)"
            rows="3"
          />
          
          {showMentions && filteredUsers.length > 0 && (
            <div className={styles.mentions}>
              {filteredUsers.map(user => (
                <button
                  key={user.id}
                  type="button"
                  className={styles.mentionItem}
                  onClick={() => handleMentionSelect(user)}
                >
                  <div className={styles.mentionAvatar}>
                    {user.avatar ? (
                      <img src={user.avatar} alt={user.name} />
                    ) : (
                      <span>{user.name.charAt(0).toUpperCase()}</span>
                    )}
                  </div>
                  <span>{user.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className={styles.formActions}>
          <span className={styles.hint}>Tip: Use @ to mention team members</span>
          <button
            type="submit"
            className={styles.submitButton}
            disabled={!newComment.trim() || isSubmitting}
          >
            {isSubmitting ? 'Posting...' : 'Post Comment'}
          </button>
        </div>
      </form>

      <div className={styles.commentsList}>
        {comments.length === 0 ? (
          <div className={styles.empty}>No comments yet. Be the first to comment!</div>
        ) : (
          comments.map(comment => (
            <div key={comment.id} className={styles.comment}>
              <div className={styles.commentHeader}>
                <div className={styles.commentAuthor}>
                  <div className={styles.avatar}>
                    {comment.author?.avatar ? (
                      <img src={comment.author.avatar} alt={comment.author.name} />
                    ) : (
                      <span>{comment.author?.name?.charAt(0).toUpperCase() || 'U'}</span>
                    )}
                  </div>
                  <div>
                    <div className={styles.authorName}>{comment.author?.name || 'Unknown'}</div>
                    <div className={styles.commentDate}>{formatDate(comment.createdAt)}</div>
                  </div>
                </div>
                <button
                  className={styles.deleteButton}
                  onClick={() => handleDelete(comment.id)}
                  title="Delete comment"
                >
                  ×
                </button>
              </div>
              <div
                className={styles.commentText}
                dangerouslySetInnerHTML={{ __html: formatCommentText(comment.text) }}
              />
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default TaskComments;
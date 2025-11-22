import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import PropTypes from 'prop-types';
import styles from './RichTextEditor.module.css';

function RichTextEditor({ value, onChange, placeholder }) {
  const [isPreview, setIsPreview] = useState(false);
  
  const handleBold = () => {
    const selection = window.getSelection().toString();
    const newValue = value.replace(selection, `**${selection}**`);
    onChange(newValue);
  };
  
  const handleItalic = () => {
    const selection = window.getSelection().toString();
    const newValue = value.replace(selection, `*${selection}*`);
    onChange(newValue);
  };
  
  const handleLink = () => {
    const url = prompt('Enter URL:');
    if (url) {
      const selection = window.getSelection().toString();
      const newValue = value.replace(selection, `[${selection}](${url})`);
      onChange(newValue);
    }
  };
  
  return (
    <div className={styles.editor}>
      <div className={styles.toolbar}>
        <button
          type="button"
          className={styles.toolbarButton}
          onClick={handleBold}
          title="Bold"
        >
          <strong>B</strong>
        </button>
        
        <button
          type="button"
          className={styles.toolbarButton}
          onClick={handleItalic}
          title="Italic"
        >
          <em>I</em>
        </button>
        
        <button
          type="button"
          className={styles.toolbarButton}
          onClick={handleLink}
          title="Link"
        >
          Link
        </button>
        
        <div className={styles.divider} />
        
        <button
          type="button"
          className={`${styles.toolbarButton} ${isPreview ? styles.active : ''}`}
          onClick={() => setIsPreview(!isPreview)}
        >
          {isPreview ? 'Edit' : 'Preview'}
        </button>
      </div>
      
      {isPreview ? (
        <div className={styles.preview}>
          <ReactMarkdown>{value}</ReactMarkdown>
        </div>
      ) : (
        <textarea
          className={styles.textarea}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
        />
      )}
    </div>
  );
}

RichTextEditor.propTypes = {
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  placeholder: PropTypes.string,
};

RichTextEditor.defaultProps = {
  placeholder: 'Write something...',
};

export default RichTextEditor;
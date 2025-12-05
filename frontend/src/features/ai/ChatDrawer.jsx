import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Send, Sparkles, Bot, Minus, ThumbsUp, ThumbsDown, Copy } from 'lucide-react';
import { api } from '../../services/api';
import { toast } from 'react-hot-toast';
import styles from './ChatDrawer.module.css';

const SUGGESTIONS = [
  "Summarize project progress",
  "What should I work on today?",
  "Identify bottlenecks",
  "Create tasks from description"
];

const ChatDrawer = ({ projectContextId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [messages, setMessages] = useState([
    { id: 'intro', role: 'ai', text: 'Hi! I\'m CollabAI. How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  
  const messagesEndRef = useRef(null);
  const location = useLocation();
  const params = useParams();

  // --- SCROLL TO BOTTOM ---
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen, isMinimized]);

  // --- FETCH USAGE QUOTA ---
  const { data: usage } = useQuery({
    queryKey: ['aiUsage'],
    queryFn: async () => {
        try {
            const res = await api.get('/ai/usage/');
            return res.data;
        } catch {
            return { used: 8, limit: 100 }; // Mock
        }
    },
    enabled: isOpen // Only fetch when open
  });

  // --- SEND MESSAGE MUTATION ---
  const chatMutation = useMutation({
    mutationFn: async (text) => {
      // Construct context based on current route
      const contextData = {
         page: location.pathname,
         projectId: params.id || null,
         workspaceContext: projectContextId
      };

      const res = await api.post('/ai/assistant/chat/', { 
        message: text, 
        context: contextData 
      });
      return res.data;
    },
    onSuccess: (res) => {
      const aiText = res.response || "I processed that, but have no specific reply.";
      setMessages(prev => [...prev, { id: Date.now(), role: 'ai', text: aiText }]);
    },
    onError: () => {
      setMessages(prev => [...prev, { id: Date.now(), role: 'ai', text: "Sorry, I'm having trouble connecting to the AI brain right now." }]);
    }
  });

  // --- HANDLERS ---
  const handleSend = (text = input) => {
    if (!text.trim()) return;

    // Add User Message
    const userMsg = { id: Date.now(), role: 'user', text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    
    // Send to API
    chatMutation.mutate(text);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Simple Markdown-ish renderer
  const renderMessage = (text) => {
      // If text contains code block (```)
      if (text.includes('```')) {
          const parts = text.split('```');
          return parts.map((part, i) => {
              if (i % 2 === 1) { // Code block
                  return <div key={i} className={styles.codeBlock}>{part}</div>;
              }
              return <span key={i}>{part}</span>;
          });
      }
      return text;
  };

  return (
    <>
      {/* Floating Action Button */}
      {!isOpen && (
        <motion.button
          className={`${styles.fab} ${styles.fabPulse}`}
          onClick={() => { setIsOpen(true); setIsMinimized(false); }}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          <Sparkles size={24} />
        </motion.button>
      )}

      {/* Chat Panel */}
      <AnimatePresence>
        {isOpen && !isMinimized && (
          <motion.div
            className={styles.drawer}
            initial={{ opacity: 0, x: 50, y: 50 }}
            animate={{ opacity: 1, x: 0, y: 0 }}
            exit={{ opacity: 0, x: 50, y: 50 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            {/* Header */}
            <div className={styles.header}>
              <div className={styles.titleRow}>
                <div style={{ background: 'linear-gradient(135deg, #6366f1, #a855f7)', padding: '6px', borderRadius: '8px', color: 'white' }}>
                  <Bot size={18} />
                </div>
                <span>AI Assistant</span>
              </div>
              <div className={styles.headerActions}>
                <button className={styles.iconBtn} onClick={() => setIsMinimized(true)} title="Minimize">
                  <Minus size={18} />
                </button>
                <button className={styles.iconBtn} onClick={() => setIsOpen(false)} title="Close">
                  <X size={18} />
                </button>
              </div>
            </div>

            {/* Usage Indicator */}
            <div className={styles.usageBar}>
               <div className={styles.usageText}>
                  <Sparkles size={12} className="text-purple-500" />
                  <span>{usage?.used || 0} / {usage?.limit || 100} messages today</span>
               </div>
            </div>

            {/* Messages Area */}
            <div className={styles.messageList}>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`${styles.message} ${msg.role === 'user' ? styles.userMessage : styles.aiMessage}`}
                >
                  {renderMessage(msg.text)}
                  {msg.role === 'ai' && msg.id !== 'intro' && (
                      <div style={{ display:'flex', gap:'0.5rem', marginTop:'0.5rem', justifyContent:'flex-end' }}>
                          <button className={styles.iconBtn} onClick={() => { navigator.clipboard.writeText(msg.text); toast.success('Copied'); }}>
                              <Copy size={12} />
                          </button>
                          <button className={styles.iconBtn}><ThumbsUp size={12} /></button>
                          <button className={styles.iconBtn}><ThumbsDown size={12} /></button>
                      </div>
                  )}
                </div>
              ))}
              
              {chatMutation.isPending && (
                <div className={styles.typingIndicator}>
                  <div className={styles.dot} />
                  <div className={styles.dot} />
                  <div className={styles.dot} />
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Suggestions */}
            <div className={styles.suggestions}>
               {SUGGESTIONS.map(s => (
                   <button key={s} className={styles.suggestionChip} onClick={() => handleSend(s)}>
                       {s}
                   </button>
               ))}
            </div>

            {/* Input Footer */}
            <div className={styles.footer}>
              <div className={styles.inputWrapper}>
                  <textarea
                    className={styles.chatInput}
                    placeholder="Ask anything..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    rows={1}
                  />
              </div>
              <button 
                className={styles.sendBtn} 
                onClick={() => handleSend()}
                disabled={!input.trim() || chatMutation.isPending}
              >
                <Send size={18} />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Minimized State (Optional Bubble) */}
      {isOpen && isMinimized && (
          <motion.button
            className={styles.fab}
            style={{ background: '#1e293b' }} // Darker when active but minimized
            onClick={() => setIsMinimized(false)}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
          >
            <Bot size={24} />
          </motion.button>
      )}
    </>
  );
};

export default ChatDrawer;
import React, { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, X, Send, Search, Sparkles, Bot } from 'lucide-react';
import { api } from '../../services/api';
import styles from './ChatDrawer.module.css';

const ChatDrawer = ({ projectContextId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { id: 'intro', role: 'ai', text: 'Hi! I\'m CollabAI. Ask me anything about your project.' }
  ]);
  const [input, setInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isOpen]);

  // --- MUTATIONS ---

  // 1. Send Chat Message
  const chatMutation = useMutation({
    mutationFn: (message) => api.post('/ai/assistant/chat/', { 
      message, 
      context: projectContextId 
    }),
    onSuccess: (res) => {
      // Append AI response
      const aiResponse = res.data.response || "I processed that, but have no specific reply.";
      setMessages(prev => [...prev, { id: Date.now(), role: 'ai', text: aiResponse }]);
    },
    onError: () => {
      setMessages(prev => [...prev, { id: Date.now(), role: 'ai', text: "Sorry, I'm having trouble connecting right now." }]);
    }
  });

  // 2. Context Search
  const searchMutation = useMutation({
    mutationFn: (query) => api.post('/ai/assistant/search/', { query }),
    onSuccess: (res) => {
      const results = res.data.results || [];
      const resultText = results.length > 0 
        ? `I found ${results.length} relevant items:\n` + results.map(r => `• ${r.title}`).join('\n')
        : "No relevant documents found for that search.";
      
      setMessages(prev => [...prev, { id: Date.now(), role: 'ai', text: resultText }]);
    }
  });

  // --- HANDLERS ---

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!input.trim()) return;

    const userMsg = { id: Date.now(), role: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    setInput('');
    
    chatMutation.mutate(currentInput);
  };

  const handleSearch = (e) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      setMessages(prev => [...prev, { id: Date.now(), role: 'user', text: `🔍 Searched for: "${searchQuery}"` }]);
      searchMutation.mutate(searchQuery);
      setSearchQuery('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* Floating Action Button */}
      <motion.button
        className={styles.fab}
        onClick={() => setIsOpen(!isOpen)}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </motion.button>

      {/* Chat Drawer */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            className={styles.drawer}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            {/* Header */}
            <div className={styles.header}>
              <div className={styles.titleRow}>
                <div className="p-1.5 bg-indigo-100 rounded-lg text-indigo-600">
                  <Bot size={20} />
                </div>
                <span>CollabAI</span>
              </div>
              <button className={styles.closeBtn} onClick={() => setIsOpen(false)}>
                <X size={18} />
              </button>
            </div>

            {/* Context Search Bar */}
            <div className={styles.searchArea}>
              <div className={styles.searchInputWrapper}>
                <Search size={14} className={styles.searchIcon} />
                <input
                  className={styles.searchInput}
                  placeholder="Search context or docs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={handleSearch}
                />
              </div>
            </div>

            {/* Messages */}
            <div className={styles.messageList}>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`${styles.message} ${msg.role === 'user' ? styles.userMessage : styles.aiMessage}`}
                >
                  {msg.text}
                </div>
              ))}
              
              {(chatMutation.isPending || searchMutation.isPending) && (
                <div className={styles.typingIndicator}>
                  <div className={styles.dot} />
                  <div className={styles.dot} />
                  <div className={styles.dot} />
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Footer */}
            <div className={styles.footer}>
              <textarea
                className={styles.chatInput}
                placeholder="Ask AI something..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
              />
              <button 
                className={styles.sendBtn} 
                onClick={handleSend}
                disabled={!input.trim() || chatMutation.isPending}
              >
                {chatMutation.isPending ? <Sparkles size={18} className="animate-pulse" /> : <Send size={18} />}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default ChatDrawer;
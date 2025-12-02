import React, { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Hash, Send, MessageSquare } from 'lucide-react';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import Avatar from '../../components/ui/Avatar/Avatar';
import styles from './Messaging.module.css';

const MessagingPage = () => {
  const { currentWorkspace } = useWorkspace();
  const queryClient = useQueryClient();
  const [activeChannelId, setActiveChannelId] = useState(null);
  const [messageText, setMessageText] = useState('');
  const bottomRef = useRef(null);

  // 1. Fetch Channels
  const { data: channels } = useQuery({
    queryKey: ['channels', currentWorkspace?.id],
    queryFn: async () => {
      if (!currentWorkspace) return [];
      const res = await api.get(`/messaging/channels/?workspace=${currentWorkspace.id}`);
      return res.data;
    },
    enabled: !!currentWorkspace,
    onSuccess: (data) => {
      if (!activeChannelId && data.length > 0) {
        setActiveChannelId(data[0].id);
      }
    }
  });

  // 2. Fetch Messages
  const { data: messages, isLoading: loadingMessages } = useQuery({
    queryKey: ['messages', activeChannelId],
    queryFn: async () => {
      if (!activeChannelId) return [];
      const res = await api.get(`/messaging/messages/?channel=${activeChannelId}&limit=50`);
      return res.data.reverse(); // Assuming API returns newest first, we want oldest at top for stream
    },
    enabled: !!activeChannelId,
    refetchInterval: 5000 // Polling for "real-time" (websocket would be better)
  });

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // 3. Send Message
  const sendMutation = useMutation({
    mutationFn: (text) => api.post('/messaging/messages/', { 
      channel: activeChannelId, 
      content: text 
    }),
    onSuccess: () => {
      setMessageText('');
      queryClient.invalidateQueries(['messages', activeChannelId]);
    }
  });

  const handleSend = (e) => {
    e?.preventDefault();
    if (!messageText.trim()) return;
    sendMutation.mutate(messageText);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const activeChannel = channels?.find(c => c.id === activeChannelId);

  if (!currentWorkspace) {
    return <div className="p-8 text-center text-gray-500">Please select a workspace.</div>;
  }

  return (
    <div className={styles.container}>
      {/* Sidebar */}
      <div className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <h2 className={styles.sidebarTitle}>Channels</h2>
        </div>
        <div className={styles.channelList}>
          {channels?.map(channel => (
            <div
              key={channel.id}
              className={`${styles.channelItem} ${channel.id === activeChannelId ? styles.activeChannel : ''}`}
              onClick={() => setActiveChannelId(channel.id)}
            >
              <Hash size={18} className={styles.hashtag} />
              <span>{channel.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className={styles.main}>
        {activeChannel ? (
          <>
            <div className={styles.chatHeader}>
              <h3 className={styles.channelName}>
                <Hash size={20} className="text-gray-400" />
                {activeChannel.name}
              </h3>
            </div>

            <div className={styles.messageStream}>
              {loadingMessages ? (
                <div className="flex justify-center p-4">Loading messages...</div>
              ) : messages?.map((msg) => (
                <div key={msg.id} className={styles.messageItem}>
                  <Avatar 
                    src={msg.sender.avatar} 
                    fallback={msg.sender.username[0]} 
                    className={styles.avatar}
                  />
                  <div className={styles.messageContent}>
                    <div className={styles.messageHeader}>
                      <span className={styles.author}>{msg.sender.username}</span>
                      <span className={styles.timestamp}>
                        {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                    <div className={styles.text}>{msg.content}</div>
                  </div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>

            <div className={styles.inputArea}>
              <div className={styles.inputForm}>
                <textarea
                  className={styles.textInput}
                  placeholder={`Message #${activeChannel.name}`}
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  rows={1}
                />
                <button 
                  className={styles.sendButton} 
                  onClick={handleSend}
                  disabled={!messageText.trim() || sendMutation.isPending}
                >
                  <Send size={18} />
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className={styles.emptyState}>
            <MessageSquare size={48} className="mb-4 opacity-20" />
            <p>Select a channel to start messaging</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MessagingPage;
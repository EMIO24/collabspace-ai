import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Hash, Search, Plus, User, MoreVertical, Paperclip, 
  Smile, Image as ImageIcon, Send, Info, Bell, FileText
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import { useWorkspace } from '../../context/WorkspaceContext';
import Avatar from '../../components/ui/Avatar/Avatar';
import NewDMModal from './NewDMModal';
import CreateChannelModal from './CreateChannelModal'; // NEW IMPORT
import styles from './Messaging.module.css';

const MessagingPage = () => {
  const { currentWorkspace } = useWorkspace();
  const queryClient = useQueryClient();
  
  // --- STATE ---
  const [activeId, setActiveId] = useState(null); 
  const [isDetailsOpen, setIsDetailsOpen] = useState(true);
  const [messageText, setMessageText] = useState('');
  const [activeType, setActiveType] = useState('channel'); 
  const [isNewDmOpen, setIsNewDmOpen] = useState(false);
  const [isCreateChannelOpen, setIsCreateChannelOpen] = useState(false); // NEW STATE
  const bottomRef = useRef(null);

  // ... (Keep existing Data Fetching Logic for Channels, DMs, Messages, Details) ...
  // 1. Channels
  const { data: rawChannels } = useQuery({
    queryKey: ['channels', currentWorkspace?.id],
    queryFn: async () => {
      if (!currentWorkspace) return [];
      const res = await api.get(`/messaging/channels/?workspace=${currentWorkspace.id}`);
      return res.data;
    },
    enabled: !!currentWorkspace
  });

  const channels = useMemo(() => {
    if (!rawChannels) return [];
    if (Array.isArray(rawChannels)) return rawChannels;
    return rawChannels.results || [];
  }, [rawChannels]);

  // 2. Direct Messages
  const { data: rawDms } = useQuery({
    queryKey: ['directMessages'],
    queryFn: async () => {
      try { 
          const res = await api.get('/messaging/direct-messages/');
          return res.data;
      } catch { return []; } 
    }
  });

  const dms = useMemo(() => {
    if (!rawDms) return [];
    if (Array.isArray(rawDms)) return rawDms;
    return rawDms.results || [];
  }, [rawDms]);

  // 3. Messages for Active Conversation
  const { data: rawMessages, isLoading: loadingMessages } = useQuery({
    queryKey: ['messages', activeId, activeType],
    queryFn: async () => {
      if (!activeId) return [];
      const endpoint = activeType === 'channel' 
        ? `/messaging/messages/?channel=${activeId}&limit=50`
        : `/messaging/direct-messages/${activeId}/`; 
      
      const res = await api.get(endpoint);
      return res.data;
    },
    enabled: !!activeId,
    refetchInterval: 3000 
  });

  const messages = useMemo(() => {
    let list = [];
    if (Array.isArray(rawMessages)) list = rawMessages;
    else if (rawMessages?.results) list = rawMessages.results;
    return [...list].reverse();
  }, [rawMessages]);

  // 4. Details
  const { data: itemDetails } = useQuery({
    queryKey: ['conversationDetails', activeId, activeType],
    queryFn: async () => {
      if (!activeId) return null;
      if (activeType === 'dm') {
          const dmObj = dms.find(d => d.id === activeId);
          if (dmObj && dmObj.recipient_id) {
              const res = await api.get(`/auth/users/${dmObj.recipient_id}/`);
              return { type: 'user', ...res.data };
          }
          return dmObj; 
      }
      const res = await api.get(`/messaging/channels/${activeId}/`);
      return { type: 'channel', ...res.data };
    },
    enabled: !!activeId && isDetailsOpen
  });

  // Auto-select first channel
  useEffect(() => {
    if (!activeId && channels?.length > 0) {
      setActiveId(channels[0].id);
      setActiveType('channel');
    }
  }, [channels, activeId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // --- MUTATIONS ---
  const sendMutation = useMutation({
    mutationFn: (content) => {
      const payload = { content, [activeType]: activeId };
      return api.post(activeType === 'channel' ? '/messaging/messages/' : '/messaging/direct-messages/', payload);
    },
    onSuccess: () => {
      setMessageText('');
      queryClient.invalidateQueries(['messages', activeId]);
    },
    onError: () => toast.error('Failed to send message')
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

  const handleDmCreated = (newId) => {
      setActiveId(newId);
      setActiveType('dm');
  };

  // --- HELPERS ---
  const activeItem = activeType === 'channel' 
    ? channels.find(c => c.id === activeId) 
    : dms.find(d => d.id === activeId);

  const displayTitle = activeItem?.name || activeItem?.username || 'Chat';
  
  const groupedMessages = useMemo(() => {
    if (!messages.length) return {};
    return messages.reduce((groups, msg) => {
      if (!msg || !msg.created_at) return groups;
      const date = new Date(msg.created_at).toLocaleDateString();
      if (!groups[date]) groups[date] = [];
      groups[date].push(msg);
      return groups;
    }, {});
  }, [messages]);

  if (!currentWorkspace) return <div className="p-10 text-center text-gray-500">Select a workspace to chat.</div>;

  return (
    <div className={`${styles.container} ${isDetailsOpen ? styles.containerOpen : ''}`}>
      
      {/* 1. LEFT PANEL: Navigation */}
      <div className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <div className={styles.searchWrapper}>
            <Search size={14} className={styles.searchIcon} />
            <input className={styles.searchInput} placeholder="Search channels..." />
          </div>
        </div>

        <div className={styles.navSection}>
          {/* Channels */}
          <div className={styles.sectionTitle}>
            <span>Channels</span>
            {/* ACTION WIRED UP HERE */}
            <button className={styles.addBtn} onClick={() => setIsCreateChannelOpen(true)}>
                <Plus size={14}/>
            </button>
          </div>
          {channels.map(c => (
            <div 
              key={c.id} 
              className={`${styles.navItem} ${activeId === c.id ? styles.activeItem : ''}`}
              onClick={() => { setActiveId(c.id); setActiveType('channel'); }}
            >
              <div className={styles.itemInfo}>
                 <Hash size={16} color="#94a3b8" />
                 <span className={styles.itemName}>{c.name}</span>
              </div>
              {c.unread_count > 0 && <span className={styles.unreadBadge}>{c.unread_count}</span>}
            </div>
          ))}

          {/* DMs */}
          <div className={styles.sectionTitle} style={{marginTop:'1.5rem'}}>
            <span>Direct Messages</span>
            <button className={styles.addBtn} onClick={() => setIsNewDmOpen(true)}>
               <Plus size={14}/>
            </button>
          </div>
          {dms.map(dm => (
             <div 
               key={dm.id} 
               className={`${styles.navItem} ${activeId === dm.id ? styles.activeItem : ''}`}
               onClick={() => { setActiveId(dm.id); setActiveType('dm'); }}
             >
               <div className={styles.itemInfo}>
                  <div className={`${styles.statusDot} ${dm.is_online ? styles.online : styles.busy}`} />
                  <Avatar src={dm.avatar} fallback={dm.username?.[0]} size="xs" />
                  <span className={styles.itemName}>{dm.username}</span>
               </div>
             </div>
          ))}
        </div>
      </div>

      {/* 2. CENTER PANEL: Chat Feed */}
      <div className={styles.chatArea}>
         {/* ... (Same as previous: Header, Messages, Composer) ... */}
         <div className={styles.chatHeader}>
            <div className={styles.headerInfo}>
               <h2>
                 {activeType === 'channel' ? <Hash size={20} className="text-gray-400" /> : <User size={20} className="text-gray-400" />}
                 {displayTitle}
               </h2>
               <p className={styles.headerSub}>
                 {activeType === 'channel' ? `${itemDetails?.members_count || 0} members` : 'Direct Message'}
               </p>
            </div>
            <div className={styles.headerActions}>
               <button 
                 className={`${styles.iconBtn} ${isDetailsOpen ? styles.activeIconBtn : ''}`}
                 onClick={() => setIsDetailsOpen(!isDetailsOpen)}
               >
                 <Info size={18} />
               </button>
            </div>
         </div>

         <div className={styles.feed}>
            {loadingMessages ? (
               <div className="text-center text-gray-400 mt-10">Loading history...</div>
            ) : Object.entries(groupedMessages).map(([date, msgs]) => (
               <React.Fragment key={date}>
                  <div className={styles.dateSeparator}>{date}</div>
                  {msgs.map(msg => {
                     const isOwn = msg.sender?.id === 'current-user-id'; 
                     return (
                       <div key={msg.id} className={`${styles.messageGroup} ${isOwn ? styles.ownMessage : ''}`}>
                          {!isOwn && (
                            <Avatar src={msg.sender?.avatar} fallback={msg.sender?.username?.[0] || '?'} className={styles.avatar} />
                          )}
                          <div className={styles.messageContent}>
                             {!isOwn && (
                               <div className={styles.senderInfo}>
                                  {msg.sender?.username} 
                                  <span className={styles.timestamp}>
                                    {new Date(msg.created_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}
                                  </span>
                               </div>
                             )}
                             <div className={styles.bubble}>
                                {msg.content}
                             </div>
                          </div>
                       </div>
                     );
                  })}
               </React.Fragment>
            ))}
            <div ref={bottomRef} />
         </div>

         <div className={styles.composer}>
            <div className={styles.composerBox}>
               <div className={styles.toolbar}>
                  <button className={styles.toolBtn}><b>B</b></button>
                  <div style={{flex:1}} />
                  <button className={styles.toolBtn}><Paperclip size={16}/></button>
               </div>
               <textarea 
                  className={styles.textarea}
                  placeholder={`Message ${displayTitle}`}
                  value={messageText}
                  onChange={e => setMessageText(e.target.value)}
                  onKeyDown={handleKeyDown}
               />
               <div className={styles.composerFooter}>
                  <button className={styles.toolBtn}><Smile size={18}/></button>
                  <button className={styles.sendBtn} onClick={handleSend} disabled={!messageText.trim() || sendMutation.isPending}>
                     <Send size={16} />
                  </button>
               </div>
            </div>
         </div>
      </div>

      {/* 3. RIGHT PANEL: Details */}
      {isDetailsOpen && (
        <div className={styles.detailsPanel}>
           {/* ... (Same as previous: Details Panel) ... */}
           <div className={styles.detailsHeader}>
              <div className="mx-auto w-20 h-20 rounded-2xl flex items-center justify-center mb-4 bg-gray-100">
                 {activeType === 'channel' ? <Hash size={40} className="text-gray-400"/> : <Avatar src={itemDetails?.avatar} fallback={itemDetails?.username?.[0]} size="lg" />}
              </div>
              <h3 className={styles.detailTitle}>{displayTitle}</h3>
           </div>
        </div>
      )}

      {/* Modals */}
      {isNewDmOpen && <NewDMModal onClose={() => setIsNewDmOpen(false)} onDmCreated={handleDmCreated} />}
      {isCreateChannelOpen && <CreateChannelModal onClose={() => setIsCreateChannelOpen(false)} />}
    </div>
  );
};

export default MessagingPage;
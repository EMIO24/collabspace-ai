import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Shield, Smartphone, Globe, Trash2, CheckCircle } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Input from '../../components/ui/Input/Input';
import Button from '../../components/ui/Button/Button';
import styles from './SecuritySettings.module.css';

const SecuritySettings = () => {
  // --- PASSWORD CHANGE ---
  const [passwords, setPasswords] = useState({ current: '', new: '', confirm: '' });
  
  const passwordMutation = useMutation({
    mutationFn: (data) => api.post('/auth/change-password/', data),
    onSuccess: () => {
      toast.success('Password changed successfully');
      setPasswords({ current: '', new: '', confirm: '' });
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Failed to change password')
  });

  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    if (passwords.new !== passwords.confirm) return toast.error("New passwords don't match");
    passwordMutation.mutate({ old_password: passwords.current, new_password: passwords.new });
  };

  // --- 2FA SETUP ---
  const [is2FAEnabled, setIs2FAEnabled] = useState(false);
  const [qrCode, setQrCode] = useState(null);
  const [otp, setOtp] = useState('');

  const enable2FAMutation = useMutation({
    mutationFn: () => api.post('/auth/2fa/enable/'),
    onSuccess: (res) => setQrCode(res.data.qr_code_url)
  });

  const verify2FAMutation = useMutation({
    mutationFn: (code) => api.post('/auth/2fa/verify-setup/', { token: code }),
    onSuccess: () => {
      toast.success('Two-Factor Authentication Enabled!');
      setIs2FAEnabled(true);
      setQrCode(null);
    },
    onError: () => toast.error('Invalid code')
  });

  // --- ACTIVE SESSIONS ---
  const { data: sessions, refetch: refetchSessions } = useQuery({
    queryKey: ['sessions'],
    queryFn: async () => (await api.get('/auth/sessions/')).data
  });

  const revokeSessionMutation = useMutation({
    mutationFn: (id) => api.delete(`/auth/sessions/${id}/`),
    onSuccess: () => {
      toast.success('Session revoked');
      refetchSessions();
    }
  });

  return (
    <div>
      <div className={styles.pageHeader}>
        <h2 className={styles.title}>Security</h2>
        <p className={styles.subtitle}>Manage your password and security preferences.</p>
      </div>

      {/* Change Password */}
      <div className={styles.section}>
        <h3 className={styles.sectionHeader}><Shield size={20} /> Change Password</h3>
        <form onSubmit={handlePasswordSubmit} className={styles.passwordForm}>
          <Input 
            type="password" label="Current Password" 
            value={passwords.current} 
            onChange={e => setPasswords({...passwords, current: e.target.value})} 
          />
          <Input 
            type="password" label="New Password" 
            value={passwords.new} 
            onChange={e => setPasswords({...passwords, new: e.target.value})} 
          />
          <Input 
            type="password" label="Confirm New Password" 
            value={passwords.confirm} 
            onChange={e => setPasswords({...passwords, confirm: e.target.value})} 
          />
          <Button type="submit" isLoading={passwordMutation.isPending}>Update Password</Button>
        </form>
      </div>

      {/* 2FA Section */}
      <div className={`${styles.section} ${styles.sectionBorder}`}>
        <h3 className={styles.sectionHeader}><Smartphone size={20} /> Two-Factor Authentication</h3>
        
        {!is2FAEnabled ? (
          <div>
            <p className={styles.helpText}>Protect your account with an extra layer of security.</p>
            {!qrCode ? (
              <Button onClick={() => enable2FAMutation.mutate()} isLoading={enable2FAMutation.isPending}>
                Enable 2FA
              </Button>
            ) : (
              <div className={styles.qrBox}>
                <img src={qrCode} alt="2FA QR Code" className={styles.qrImage} />
                <p className={styles.helpText}>Scan this with Google Authenticator</p>
                <div className={styles.verifyRow}>
                  <Input 
                    placeholder="Enter 6-digit code" 
                    value={otp} 
                    onChange={e => setOtp(e.target.value)} 
                  />
                  <Button onClick={() => verify2FAMutation.mutate(otp)}>Verify</Button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className={styles.successBox}>
            <CheckCircle size={20} /> 2FA is currently enabled on your account.
          </div>
        )}
      </div>

      {/* Active Sessions */}
      <div className={`${styles.section} ${styles.sectionBorder}`}>
        <h3 className={styles.sectionHeader}><Globe size={20} /> Active Sessions</h3>
        <div className={styles.sessionList}>
          {sessions?.map(session => (
            <div key={session.id} className={styles.sessionItem}>
              <div className={styles.sessionInfo}>
                <h4>{session.device || 'Unknown Device'}</h4>
                <p className={styles.sessionMeta}>
                  {session.ip_address} • Last active: {new Date(session.last_active).toLocaleDateString()}
                </p>
              </div>
              <button 
                onClick={() => revokeSessionMutation.mutate(session.id)}
                className={styles.revokeBtn}
                title="Revoke Session"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
          {!sessions?.length && <p className={styles.helpText}>No active sessions found.</p>}
        </div>
      </div>
    </div>
  );
};

export default SecuritySettings;
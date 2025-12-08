import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Shield, Smartphone, Globe, Trash2, CheckCircle, Copy, Key } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { api } from '../../services/api';
import Input from '../../components/ui/Input/Input';
import Button from '../../components/ui/Button/Button';
import styles from './SecuritySettings.module.css';

const SecuritySettings = () => {
  const queryClient = useQueryClient();
  
  // --- 2FA STATE ---
  const [is2FAEnabled, setIs2FAEnabled] = useState(false);
  const [setupStep, setSetupStep] = useState(0); // 0: Init, 1: Scan, 2: Backup
  const [qrCode, setQrCode] = useState(null);
  const [secretKey, setSecretKey] = useState(null); 
  const [otp, setOtp] = useState('');
  const [confirmPassword, setConfirmPassword] = useState(''); 
  const [backupCodes, setBackupCodes] = useState([]);

  // 1. Fetch Auth Status
  useQuery({
    queryKey: ['authCheck'],
    queryFn: async () => {
      try {
        const res = await api.get('/auth/check/');
        setIs2FAEnabled(res.data.two_factor_enabled);
        return res.data;
      } catch { return {}; }
    }
  });

  // 2. Enable 2FA (Requires Password)
  const enable2FA = useMutation({
    mutationFn: (password) => api.post('/auth/2fa/enable/', { password }),
    onSuccess: (res) => {
        const data = res.data;
        
        let imgData = data.qr_code_url || data.qr_code || data.image;
        if (imgData && !imgData.startsWith('http') && !imgData.startsWith('data:')) {
            imgData = `data:image/png;base64,${imgData}`;
        }
        
        setQrCode(imgData);
        setSecretKey(data.secret || data.key || data.otp_secret);
        
        setSetupStep(1); 
        setConfirmPassword('');
        toast.success("Password confirmed.");
    },
    onError: (err) => {
        // FIX: Check if already enabled and sync state
        const errorData = err.response?.data;
        const msg = errorData?.message || errorData?.error || 'Incorrect password';
        
        if (msg.includes('already enabled')) {
            setIs2FAEnabled(true);
            toast.success("2FA is already enabled on your account.");
        } else {
            toast.error(msg);
        }
    }
  });

  const verify2FA = useMutation({
    // FIX: Changed 'token' to 'code' based on backend error message
    mutationFn: (code) => api.post('/auth/2fa/verify-setup/', { code }),
    onSuccess: (res) => {
      toast.success('2FA Verified!');
      setIs2FAEnabled(true);
      setBackupCodes(res.data.backup_codes || ['SAVE-THESE-CODES', 'FOR-RECOVERY']); 
      setSetupStep(2); 
    },
    onError: () => toast.error('Invalid Verification Code')
  });

  const disable2FA = useMutation({
    mutationFn: () => api.post('/auth/2fa/disable/', { code: otp, password: confirmPassword }),
    onSuccess: () => {
      toast.success('2FA Disabled');
      setIs2FAEnabled(false);
      setSetupStep(0);
      setOtp('');
      setConfirmPassword('');
    },
    onError: () => toast.error('Failed to disable 2FA. Check code or password.')
  });

  // --- SESSIONS ---
  const { data: rawSessions, refetch: refetchSessions } = useQuery({
    queryKey: ['sessions'],
    queryFn: async () => {
      try { return (await api.get('/auth/sessions/')).data; } catch { return []; }
    }
  });

  const sessions = useMemo(() => {
    if (!rawSessions) return [];
    if (Array.isArray(rawSessions)) return rawSessions;
    return rawSessions.results || [];
  }, [rawSessions]);

  const revokeSession = useMutation({
    mutationFn: (id) => api.delete(`/auth/sessions/${id}/`),
    onSuccess: () => { toast.success('Session revoked'); refetchSessions(); }
  });

  const revokeAll = useMutation({
    mutationFn: () => api.post('/auth/sessions/revoke-all/'),
    onSuccess: () => { toast.success('All other sessions signed out'); refetchSessions(); }
  });

  const copySecret = () => {
    if (secretKey) {
        navigator.clipboard.writeText(secretKey);
        toast.success("Secret key copied");
    }
  };

  return (
    <div className={styles.container}>
      {/* --- 2FA Section --- */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
           <h3 className={styles.cardTitle}>
             <Shield size={20} className="text-green-600"/> Two-Factor Authentication
           </h3>
           <span className={`${styles.badge} ${is2FAEnabled ? styles.badgeGreen : styles.badgeGray}`}>
              {is2FAEnabled ? 'Enabled' : 'Disabled'}
           </span>
        </div>

        {!is2FAEnabled ? (
          <div>
            {setupStep === 0 && (
               <div className="flex flex-col items-start gap-4 max-w-sm">
                  <p className="text-gray-600 text-sm">
                    Enter your current password to begin 2FA setup.
                  </p>
                  <div className="w-full">
                    <Input 
                      type="password" 
                      placeholder="Current Password" 
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                    />
                  </div>
                  <Button 
                    onClick={() => enable2FA.mutate(confirmPassword)} 
                    isLoading={enable2FA.isPending}
                    disabled={!confirmPassword}
                  >
                    Start Setup
                  </Button>
               </div>
            )}
            
            {setupStep === 1 && (
               <div className={styles.wizardStep}>
                  <h4 className={styles.stepTitle}>Scan QR Code</h4>
                  <p className={styles.stepDesc}>Open Google Authenticator or Authy and scan this code.</p>
                  
                  <div className={styles.qrBox}>
                     {qrCode ? (
                        <img src={qrCode} alt="QR Code" className={styles.qrImage} />
                     ) : (
                        <div className="h-40 w-40 flex items-center justify-center bg-gray-100 text-gray-400 rounded">
                           No Image
                        </div>
                     )}
                  </div>

                  {/* Manual Key Fallback */}
                  {secretKey && (
                     <div className="flex items-center gap-2 mb-6 bg-white px-3 py-2 rounded border border-gray-200">
                        <Key size={14} className="text-gray-400" />
                        <code className="text-xs font-mono font-bold text-gray-700">{secretKey}</code>
                        <button onClick={copySecret} className="text-blue-500 hover:text-blue-700 ml-2" title="Copy Key">
                           <Copy size={14} />
                        </button>
                     </div>
                  )}

                  <div className={styles.codeGroup}>
                     <Input 
                        className={styles.codeInput} 
                        placeholder="123456" 
                        maxLength={6}
                        value={otp}
                        onChange={e => setOtp(e.target.value)}
                     />
                     <Button onClick={() => verify2FA.mutate(otp)} isLoading={verify2FA.isPending}>Verify</Button>
                  </div>
               </div>
            )}
          </div>
        ) : (
          <div>
             {setupStep === 2 ? (
                <div className={styles.wizardStep}>
                   <h4 className={styles.stepTitle}>Backup Codes</h4>
                   <p className={styles.stepDesc}>Save these codes securely. You can use them to log in if you lose your phone.</p>
                   <div className={styles.backupGrid}>
                      {backupCodes.map((c, i) => <div key={i}>{c}</div>)}
                   </div>
                   <Button variant="ghost" onClick={() => setSetupStep(0)}>Done</Button>
                </div>
             ) : (
                <div className="flex flex-col gap-6">
                   <div className="flex items-center gap-3 bg-green-50 p-4 rounded-xl border border-green-100">
                      <CheckCircle className="text-green-600" />
                      <div>
                         <p className="font-bold text-green-800 text-sm">2FA is active</p>
                         <p className="text-green-700 text-xs">Your account is protected.</p>
                      </div>
                   </div>
                   
                   <div className="border-t pt-4">
                      <h4 className="font-bold text-sm text-gray-700 mb-2">Disable 2FA</h4>
                      <p className="text-xs text-gray-500 mb-2">Enter your password to disable protection.</p>
                      <div className="flex flex-col gap-2 max-w-sm">
                         <Input 
                            type="password"
                            placeholder="Current Password" 
                            value={confirmPassword} 
                            onChange={e => setConfirmPassword(e.target.value)} 
                         />
                         <div className="flex gap-2">
                           <Input 
                              placeholder="2FA Code (Optional)" 
                              value={otp} 
                              onChange={e => setOtp(e.target.value)} 
                           />
                           <button 
                              className={styles.disableBtn}
                              onClick={() => disable2FA.mutate()}
                              disabled={!confirmPassword}
                           >
                              Disable
                           </button>
                         </div>
                      </div>
                   </div>
                </div>
             )}
          </div>
        )}
      </div>

      {/* --- Active Sessions --- */}
      <div className={styles.card}>
         <div className={styles.cardHeader}>
            <h3 className={styles.cardTitle}><Globe size={20} className="text-blue-500"/> Active Sessions</h3>
            <button 
               className="text-xs text-red-500 hover:underline font-bold"
               onClick={() => { if(confirm('Log out everywhere else?')) revokeAll.mutate() }}
            >
               Sign Out All Others
            </button>
         </div>

         <div className={styles.sessionList}>
            {sessions.map(session => (
               <div key={session.id} className={styles.sessionItem}>
                  <div className={styles.sessionIcon}>
                     {session.device_type === 'mobile' ? <Smartphone size={20}/> : <Globe size={20}/>}
                  </div>
                  <div className="flex-1">
                     <div className="flex items-center gap-2">
                        <span className="font-semibold text-sm text-gray-800">{session.device || 'Unknown Device'}</span>
                        {session.is_current && <span className={styles.currentBadge}>CURRENT</span>}
                     </div>
                     <div className="text-xs text-gray-500">
                        {session.ip_address} • {session.location || 'Unknown Location'} • Last active: {new Date(session.last_active).toLocaleString()}
                     </div>
                  </div>
                  {!session.is_current && (
                     <button className={styles.revokeBtn} onClick={() => revokeSession.mutate(session.id)}>Sign Out</button>
                  )}
               </div>
            ))}
            {!sessions.length && <div className="text-center text-gray-400 text-sm py-4">No active sessions found.</div>}
         </div>
      </div>
    </div>
  );
};

export default SecuritySettings;
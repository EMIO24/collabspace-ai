import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { api } from '../../services/api';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import styles from './Integrations.module.css'; // Reusing generic styles

const OAuthCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('processing'); // processing, success, error

  useEffect(() => {
    const code = searchParams.get('code');
    const processCallback = async () => {
      if (!code) {
        setStatus('error');
        return;
      }

      try {
        // 3. OAuth Callback
        await api.get(`/integrations/oauth/github/callback/?code=${code}`);
        setStatus('success');
        setTimeout(() => navigate('/settings/integrations'), 2000);
      } catch (error) {
        console.error("OAuth Error", error);
        setStatus('error');
      }
    };

    processCallback();
  }, [searchParams, navigate]);

  return (
    <div style={{ 
      height: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      flexDirection: 'column',
      gap: '1rem'
    }}>
      {status === 'processing' && (
        <>
          <Loader2 size={48} className="animate-spin text-blue-500" />
          <h2 className={styles.name}>Connecting to GitHub...</h2>
        </>
      )}
      
      {status === 'success' && (
        <>
          <CheckCircle size={48} className="text-green-500" />
          <h2 className={styles.name}>Successfully Connected!</h2>
          <p className={styles.subtitle}>Redirecting you back...</p>
        </>
      )}

      {status === 'error' && (
        <>
          <XCircle size={48} className="text-red-500" />
          <h2 className={styles.name}>Connection Failed</h2>
          <p className={styles.subtitle}>Please try again.</p>
          <button 
            onClick={() => navigate('/settings/integrations')}
            style={{ marginTop: '1rem', textDecoration: 'underline', color: 'var(--primary)' }}
          >
            Return to Settings
          </button>
        </>
      )}
    </div>
  );
};

export default OAuthCallback;
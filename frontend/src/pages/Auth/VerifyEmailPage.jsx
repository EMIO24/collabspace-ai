import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import AuthLayout from '@components/auth/AuthLayout';
import Button from '@components/common/Button';
import styles from './VerifyEmailPage.module.css';
import { verifyEmail } from '@api/auth';

export default function VerifyEmailPage() {
  const [search] = useSearchParams();
  const token = search.get('token');
  const [status, setStatus] = useState('loading');
  const navigate = useNavigate();

  useEffect(() => {
    async function verify() {
      try {
        await verifyEmail(token);
        setStatus('success');
      } catch (err) {
        setStatus('error');
      }
    }
    verify();
  }, [token]);

  return (
    <AuthLayout title="Verify email">
      <div className={styles.wrap}>
        {status === 'loading' && <p>Verifying your email...</p>}
        {status === 'success' && (
          <>
            <p>Your email is verified. You can now sign in.</p>
            <Button onClick={() => navigate('/login')} variant="primary">Go to login</Button>
          </>
        )}
        {status === 'error' && (
          <>
            <p>Verification failed or link expired.</p>
            <Button onClick={() => navigate('/register')}>Register</Button>
          </>
        )}
      </div>
    </AuthLayout>
  );
}

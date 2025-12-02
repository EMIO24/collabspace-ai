import React, { useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import Card from '../../components/ui/Card/Card';
import Button from '../../components/ui/Button/Button';
// CORRECTED IMPORT PATH
import styles from '../../layout/AuthLayout/AuthLayout.module.css';

const VerifyEmail = () => {
  const { key } = useParams();

  const mutation = useMutation({
    mutationFn: (data) => axios.post('http://localhost:8000/api/auth/verify-email/', data),
  });

  useEffect(() => {
    if (key) {
      mutation.mutate({ key });
    }
  }, [key]);

  const renderContent = () => {
    if (mutation.isPending) {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '2rem 0' }}>
          <Loader2 className="animate-spin text-blue-600 mb-4" size={48} />
          <p style={{ color: 'var(--text-muted)' }}>Verifying your email address...</p>
        </div>
      );
    }

    if (mutation.isError) {
      return (
        <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem', color: 'var(--danger)' }}>
            <XCircle size={56} />
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.5rem' }}>
            Verification Failed
          </h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
            The verification link is invalid or has expired.
          </p>
          <Link to="/login">
            <Button variant="ghost">Return to Login</Button>
          </Link>
        </div>
      );
    }

    if (mutation.isSuccess) {
      return (
        <div style={{ textAlign: 'center', padding: '1.5rem 0' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem', color: 'var(--success)' }}>
            <CheckCircle2 size={56} />
          </div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.5rem' }}>
            Email Verified!
          </h2>
          <p style={{ color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
            Your account has been successfully verified. You can now access the platform.
          </p>
          <Link to="/login">
            <Button className="w-full">Continue to Login</Button>
          </Link>
        </div>
      );
    }

    return null;
  };

  return (
    <Card className={styles.authCard}>
      {renderContent()}
    </Card>
  );
};

export default VerifyEmail;
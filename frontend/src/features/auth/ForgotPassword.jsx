import React, { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { Mail, Lock, CheckCircle, ArrowLeft } from 'lucide-react';
import { toast } from 'react-hot-toast';
import axios from 'axios';
import Card from '../../components/ui/Card/Card';
import Button from '../../components/ui/Button/Button';
import Input from '../../components/ui/Input/Input';
// CORRECTED IMPORT PATH
import styles from '../../layout/AuthLayout/AuthLayout.module.css';

const ForgotPassword = () => {
  const { uid, token } = useParams();
  const navigate = useNavigate();
  const isConfirmMode = !!uid && !!token;

  const [email, setEmail] = useState('');
  const [passwords, setPasswords] = useState({ new_password: '', re_new_password: '' });
  const [isSuccess, setIsSuccess] = useState(false);

  const requestMutation = useMutation({
    mutationFn: (data) => axios.post('http://localhost:8000/api/auth/reset-password/', data),
    onSuccess: () => {
      setIsSuccess(true);
      toast.success('Reset link sent to your email.');
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Request failed')
  });

  const confirmMutation = useMutation({
    mutationFn: (data) => axios.post('http://localhost:8000/api/auth/reset-password-confirm/', data),
    onSuccess: () => {
      toast.success('Password reset successfully!');
      navigate('/login');
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Reset failed')
  });

  const handleRequest = (e) => {
    e.preventDefault();
    requestMutation.mutate({ email });
  };

  const handleConfirm = (e) => {
    e.preventDefault();
    if (passwords.new_password !== passwords.re_new_password) {
      toast.error("Passwords don't match");
      return;
    }
    confirmMutation.mutate({ 
      uid, 
      token, 
      new_password: passwords.new_password, 
      re_new_password: passwords.re_new_password 
    });
  };

  if (isSuccess && !isConfirmMode) {
    return (
      <Card className={`${styles.authCard}`} style={{ textAlign: 'center' }}>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem', color: 'var(--success)' }}>
          <CheckCircle size={48} />
        </div>
        <h2 className={styles.title}>Check your inbox</h2>
        <p className={styles.subtitle} style={{ marginBottom: '1.5rem' }}>
          We've sent password reset instructions to <strong>{email}</strong>.
        </p>
        <Link to="/login">
          <Button variant="ghost">Back to Login</Button>
        </Link>
      </Card>
    );
  }

  return (
    <Card className={styles.authCard}>
      <div className={styles.header}>
        <h1 className={styles.title}>
          {isConfirmMode ? 'Set New Password' : 'Reset Password'}
        </h1>
        <p className={styles.subtitle}>
          {isConfirmMode 
            ? 'Create a robust password for your account' 
            : 'Enter your email to receive reset instructions'}
        </p>
      </div>

      {isConfirmMode ? (
        <form onSubmit={handleConfirm} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <Input
            label="New Password"
            type="password"
            icon={Lock}
            required
            value={passwords.new_password}
            onChange={(e) => setPasswords({...passwords, new_password: e.target.value})}
          />
          <Input
            label="Confirm Password"
            type="password"
            icon={Lock}
            required
            value={passwords.re_new_password}
            onChange={(e) => setPasswords({...passwords, re_new_password: e.target.value})}
          />
          <Button type="submit" className="w-full mt-2" isLoading={confirmMutation.isPending}>
            Reset Password
          </Button>
        </form>
      ) : (
        <form onSubmit={handleRequest} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <Input
            label="Email Address"
            type="email"
            icon={Mail}
            placeholder="you@company.com"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <Button type="submit" className="w-full mt-2" isLoading={requestMutation.isPending}>
            Send Reset Link
          </Button>
        </form>
      )}

      <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
        <Link to="/login" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          <ArrowLeft size={16} /> Back to Login
        </Link>
      </div>
    </Card>
  );
};

export default ForgotPassword;
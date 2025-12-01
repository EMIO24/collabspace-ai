import React, { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { Mail, Lock, CheckCircle, ArrowLeft } from 'lucide-react';
import { toast } from 'react-hot-toast';
import axios from 'axios';
import Card from '../../components/ui/Card/Card';
import Button from '../../components/ui/Button/Button';
import Input from '../../components/ui/Input/Input';
import styles from '../../components/layouts/AuthLayout/AuthLayout.module.css';

const ForgotPassword = () => {
  const { uid, token } = useParams(); // If present, we are in CONFIRM mode
  const navigate = useNavigate();
  const isConfirmMode = !!uid && !!token;

  const [email, setEmail] = useState('');
  const [passwords, setPasswords] = useState({ new_password: '', re_new_password: '' });
  const [isSuccess, setIsSuccess] = useState(false);

  // Request Mutation
  const requestMutation = useMutation({
    mutationFn: (data) => axios.post('http://localhost:8000/api/auth/reset-password/', data),
    onSuccess: () => {
      setIsSuccess(true);
      toast.success('Reset link sent to your email.');
    },
    onError: (err) => toast.error(err.response?.data?.detail || 'Request failed')
  });

  // Confirm Mutation
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
      <Card className={`${styles.authCard} text-center`}>
        <div className="flex justify-center mb-4 text-green-500">
          <CheckCircle size={48} />
        </div>
        <h2 className={styles.title}>Check your inbox</h2>
        <p className="text-gray-500 mb-6">
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
        <form onSubmit={handleConfirm} className="space-y-4">
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
        <form onSubmit={handleRequest} className="space-y-4">
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

      <div className="mt-6 text-center">
        <Link to="/login" className="flex items-center justify-center gap-2 text-sm text-gray-500 hover:text-blue-600 transition-colors">
          <ArrowLeft size={16} /> Back to Login
        </Link>
      </div>
    </Card>
  );
};

export default ForgotPassword;
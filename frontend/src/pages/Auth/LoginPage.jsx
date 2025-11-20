import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { login } from '@store/slices/authSlice';
import Button from '@components/common/Button';
import Input from '@components/common/Input';
import AuthLayout from '@components/auth/AuthLayout';
import styles from './LoginPage.module.css';

export default function LoginPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { loading, error } = useSelector((s) => s.auth);
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [rememberMe, setRememberMe] = useState(false);

  const onSubmit = async (data) => {
    try {
      await dispatch(login(data)).unwrap();
      navigate('/');
    } catch (err) {
      // handled in slice, but log
      console.error('Login failed', err);
    }
  };

  return (
    <AuthLayout title="Welcome back">
      <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
        {error && <div className={styles.error}>{error.message || error || 'Login failed'}</div>}

        <Input
          id="email"
          label="Email"
          type="email"
          {...register('email', {
            required: 'Email is required',
            pattern: {
              value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
              message: 'Invalid email address',
            },
          })}
          error={errors.email?.message}
        />

        <Input
          id="password"
          label="Password"
          type="password"
          {...register('password', {
            required: 'Password is required',
            minLength: { value: 6, message: 'Minimum 6 characters' },
          })}
          error={errors.password?.message}
        />

        <div className={styles.row}>
          <label className={styles.checkbox}>
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
            />
            <span>Remember me</span>
          </label>
          <Link to="/forgot-password" className={styles.forgot}>Forgot password?</Link>
        </div>

        <Button type="submit" variant="primary" fullWidth loading={loading}>Sign in</Button>

        <div className={styles.divider}><span>or continue with</span></div>

        <div className={styles.social}>
          <button type="button" className={styles.socialBtn}><img src="/icons/google.svg" alt="Google" /> Google</button>
          <button type="button" className={styles.socialBtn}><img src="/icons/github.svg" alt="GitHub" /> GitHub</button>
        </div>

        <p className={styles.bottom}>
          Don't have an account? <Link to="/register">Sign up</Link>
        </p>
      </form>
    </AuthLayout>
  );
}

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';
import { register as registerAPI } from '@api/auth';
import Button from '@components/common/Button';
import Input from '@components/common/Input';
import PasswordStrength from '@components/auth/PasswordStrength';
import AuthLayout from '@components/auth/AuthLayout';
import styles from './RegisterPage.module.css';
import { validatePasswordStrength } from '@utils/validators';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm();
  const [serverError, setServerError] = useState(null);

  const password = watch('password', '');

  const onSubmit = async (data) => {
    setServerError(null);
    try {
      const payload = {
        first_name: data.firstName,
        last_name: data.lastName,
        username: data.username,
        email: data.email,
        password: data.password,
      };
      // use auth API (should return created user or tokens)
      const res = await registerAPI(payload);
      // if backend auto-logs in, redirect; otherwise to login
      navigate('/login');
    } catch (err) {
      setServerError(err.message || 'Registration failed');
    }
  };

  const pwCheck = validatePasswordStrength(password);

  return (
    <AuthLayout title="Create your account">
      <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
        {serverError && <div className={styles.error}>{serverError}</div>}

        <div className={styles.row2}>
          <Input
            id="firstName"
            label="First name"
            {...register('firstName', { required: 'First name required' })}
            error={errors.firstName?.message}
          />
          <Input
            id="lastName"
            label="Last name"
            {...register('lastName', { required: 'Last name required' })}
            error={errors.lastName?.message}
          />
        </div>

        <Input
          id="username"
          label="Username"
          {...register('username', { required: 'Username required', minLength: { value: 3, message: '3+ characters' } })}
          error={errors.username?.message}
        />

        <Input
          id="email"
          label="Email"
          type="email"
          {...register('email', { required: 'Email required', pattern: { value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i, message: 'Invalid email' } })}
          error={errors.email?.message}
        />

        <Input
          id="password"
          label="Password"
          type="password"
          {...register('password', { required: 'Password required', minLength: { value: 8, message: '8+ characters' } })}
          error={errors.password?.message}
        />

        <div className={styles.passwordMeta}>
          <PasswordStrength value={password} />
          <div className={styles.hint}>Use at least 8 characters, mix letters and numbers.</div>
        </div>

        <Input
          id="confirmPassword"
          label="Confirm password"
          type="password"
          {...register('confirmPassword', {
            required: 'Confirm your password',
            validate: (val) => val === password || 'Passwords do not match'
          })}
          error={errors.confirmPassword?.message}
        />

        <Button type="submit" variant="primary" fullWidth loading={isSubmitting}>Create account</Button>

        <p className={styles.bottom}>Already a member? <Link to="/login">Sign in</Link></p>
      </form>
    </AuthLayout>
  );
}

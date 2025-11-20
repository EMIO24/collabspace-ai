import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import AuthLayout from '@components/auth/AuthLayout';
import Input from '@components/common/Input';
import Button from '@components/common/Button';
import styles from './ForgotPasswordPage.module.css';
import { requestPasswordReset } from '@api/auth';

export default function ForgotPasswordPage() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm();
  const [sent, setSent] = useState(false);
  const [serverError, setServerError] = useState(null);

  const onSubmit = async ({ email }) => {
    setServerError(null);
    try {
      await requestPasswordReset(email);
      setSent(true);
    } catch (err) {
      setServerError(err.message || 'Failed to send reset email');
    }
  };

  return (
    <AuthLayout title="Reset your password">
      <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
        {serverError && <div className={styles.error}>{serverError}</div>}
        {!sent ? (
          <>
            <p className={styles.info}>Enter your email and we'll send a link to reset your password.</p>

            <Input id="email" label="Email" type="email"
              {...register('email', { required: 'Email required' })}
              error={errors.email?.message}
            />

            <Button type="submit" variant="primary" fullWidth loading={isSubmitting}>Send reset link</Button>

            <p className={styles.bottom}>Remembered? <a href="/login">Sign in</a></p>
          </>
        ) : (
          <div className={styles.sent}>
            <strong>Check your inbox</strong>
            <p>We've sent instructions to reset your password to the email provided (check spam folder).</p>
            <p className={styles.bottom}><a href="/login">Back to login</a></p>
          </div>
        )}
      </form>
    </AuthLayout>
  );
}

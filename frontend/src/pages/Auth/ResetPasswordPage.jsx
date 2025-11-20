import React, { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import Input from '@components/common/Input';
import Button from '@components/common/Button';
import AuthLayout from '@components/auth/AuthLayout';
import styles from './ResetPasswordPage.module.css';
import { confirmPasswordReset } from '@api/auth';

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm();
  const [serverError, setServerError] = useState(null);

  const onSubmit = async ({ password }) => {
    setServerError(null);
    try {
      await confirmPasswordReset(token, password);
      navigate('/login');
    } catch (err) {
      setServerError(err.message || 'Reset failed');
    }
  };

  return (
    <AuthLayout title="Choose a new password">
      <form className={styles.form} onSubmit={handleSubmit(onSubmit)} noValidate>
        {serverError && <div className={styles.error}>{serverError}</div>}

        <Input id="password" label="New password" type="password"
          {...register('password', { required: 'Password required', minLength: { value: 8, message: '8+ characters' } })}
          error={errors.password?.message}
        />

        <Input id="confirmPassword" label="Confirm password" type="password"
          {...register('confirmPassword', { required: 'Confirm password', validate: (v) => v === watch('password') || 'Passwords do not match' })}
          error={errors.confirmPassword?.message}
        />

        <Button type="submit" variant="primary" fullWidth loading={isSubmitting}>Reset password</Button>
      </form>
    </AuthLayout>
  );
}

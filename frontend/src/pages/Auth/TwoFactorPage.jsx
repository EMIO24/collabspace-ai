import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import AuthLayout from '@components/auth/AuthLayout';
import Input from '@components/common/Input';
import Button from '@components/common/Button';
import styles from './TwoFactorPage.module.css';
import { setup2FA, verify2FA } from '@api/auth';

/**
 * SMS 2FA flow:
 *  - user requests SMS code (setup2FA triggers sending code)
 *  - user enters code -> verify2FA
 *
 * Adjust API functions if your backend uses different endpoints.
 */

export default function TwoFactorPage() {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm();
  const [status, setStatus] = useState('idle'); // idle | sent | verified | error
  const [serverError, setServerError] = useState(null);

  const sendSMS = async () => {
    setServerError(null);
    try {
      await setup2FA(); // assume this triggers SMS
      setStatus('sent');
    } catch (err) {
      setServerError(err.message || 'Failed to send SMS');
    }
  };

  const onVerify = async ({ code }) => {
    setServerError(null);
    try {
      await verify2FA(code); // verify code
      setStatus('verified');
    } catch (err) {
      setServerError(err.message || 'Verification failed');
    }
  };

  return (
    <AuthLayout title="Two-factor authentication">
      <div className={styles.wrap}>
        {serverError && <div className={styles.error}>{serverError}</div>}

        {status === 'idle' && (
          <>
            <p>We will send a verification code to your phone.</p>
            <Button onClick={sendSMS} variant="primary">Send SMS code</Button>
          </>
        )}

        {status === 'sent' && (
          <>
            <p>Enter the 6-digit code we sent to your phone.</p>
            <form onSubmit={handleSubmit(onVerify)} className={styles.form}>
              <Input id="code" label="Verification code" {...register('code', { required: 'Code required', minLength: { value: 4, message: 'Code is too short' } })} error={errors.code?.message} />
              <Button type="submit" variant="primary" fullWidth loading={isSubmitting}>Verify</Button>
            </form>
            <p className={styles.hint}>Didn't receive a code? <button type="button" className={styles.linkBtn} onClick={sendSMS}>Resend</button></p>
          </>
        )}

        {status === 'verified' && (
          <>
            <p>Two-factor authentication enabled.</p>
            <Button onClick={() => window.location.href = '/'} variant="primary">Continue</Button>
          </>
        )}
      </div>
    </AuthLayout>
  );
}

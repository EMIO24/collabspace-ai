import React from 'react';
import LoginForm from '@components/auth/LoginForm/LoginForm';

export default function Login() {
  return (
    <div style={{ maxWidth: 420, margin: '40px auto' }}>
      <h1>Sign in</h1>
      <LoginForm />
    </div>
  );
}

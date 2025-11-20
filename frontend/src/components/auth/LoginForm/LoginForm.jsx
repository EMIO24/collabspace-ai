import React from 'react';
import { useForm } from 'react-hook-form';
import { useDispatch } from 'react-redux';
import { login } from '@store/slices/authSlice';
import styles from './LoginForm.module.css';

export default function LoginForm() {
  const { register, handleSubmit } = useForm();
  const dispatch = useDispatch();

  const onSubmit = data => {
    dispatch(login(data));
  };

  return (
    <form className={styles.form} onSubmit={handleSubmit(onSubmit)}>
      <label className={styles.field}>
        <span>Email</span>
        <input {...register('email', { required: true })} type="email" />
      </label>

      <label className={styles.field}>
        <span>Password</span>
        <input {...register('password', { required: true })} type="password" />
      </label>

      <button className={styles.submit} type="submit">Sign in</button>
    </form>
  );
}

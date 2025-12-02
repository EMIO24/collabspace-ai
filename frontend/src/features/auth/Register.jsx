import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { Mail, Lock, User, ArrowRight } from 'lucide-react';
import { toast } from 'react-hot-toast';
import axios from 'axios';
import Card from '../../components/ui/Card/Card';
import Button from '../../components/ui/Button/Button';
import Input from '../../components/ui/Input/Input';
// CORRECTED IMPORT PATH
import styles from '../../layout/AuthLayout/AuthLayout.module.css';

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    first_name: '',
    last_name: '',
    password: '',
    re_password: ''
  });

  const mutation = useMutation({
    mutationFn: (data) => axios.post('http://localhost:8000/api/auth/register/', data),
    onSuccess: () => {
      toast.success('Account created! Please verify your email.');
      navigate('/login');
    },
    onError: (error) => {
      const data = error.response?.data;
      if (typeof data === 'object') {
        Object.entries(data).forEach(([key, val]) => {
          toast.error(`${key}: ${val}`);
        });
      } else {
        toast.error('Registration failed');
      }
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (formData.password !== formData.re_password) {
      toast.error('Passwords do not match');
      return;
    }
    mutation.mutate(formData);
  };

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <Card className={styles.authCard}>
      <div className={styles.header}>
        <h1 className={styles.title}>Create Account</h1>
        <p className={styles.subtitle}>Join the team on CollabSpace AI</p>
      </div>

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <Input
          name="username"
          label="Username"
          icon={User}
          required
          value={formData.username}
          onChange={handleChange}
        />
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <Input
            name="first_name"
            label="First Name"
            placeholder="Jane"
            required
            value={formData.first_name}
            onChange={handleChange}
          />
          <Input
            name="last_name"
            label="Last Name"
            placeholder="Doe"
            required
            value={formData.last_name}
            onChange={handleChange}
          />
        </div>

        <Input
          name="email"
          label="Email Address"
          type="email"
          icon={Mail}
          required
          value={formData.email}
          onChange={handleChange}
        />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <Input
            name="password"
            label="Password"
            type="password"
            icon={Lock}
            required
            value={formData.password}
            onChange={handleChange}
          />
          <Input
            name="re_password"
            label="Confirm"
            type="password"
            icon={Lock}
            required
            value={formData.re_password}
            onChange={handleChange}
          />
        </div>

        <Button 
          type="submit" 
          className="w-full mt-4" 
          isLoading={mutation.isPending}
        >
          Get Started <ArrowRight size={18} />
        </Button>
      </form>

      <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
        Already have an account?{' '}
        <Link to="/login" style={{ color: 'var(--primary)', fontWeight: 600 }}>
          Sign In
        </Link>
      </div>
    </Card>
  );
};

export default Register;
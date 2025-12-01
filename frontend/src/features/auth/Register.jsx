import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { Mail, Lock, User, ArrowRight } from 'lucide-react';
import { toast } from 'react-hot-toast';
import axios from 'axios';
import Card from '../../components/ui/Card/Card';
import Button from '../../components/ui/Button/Button';
import Input from '../../components/ui/Input/Input';
import styles from '../../components/layouts/AuthLayout/AuthLayout.module.css';

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
      // Map dictionary errors (e.g. { username: ['Taken'] }) to toast
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

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          name="username"
          label="Username"
          icon={User}
          required
          value={formData.username}
          onChange={handleChange}
        />
        
        <div className="grid grid-cols-2 gap-4">
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

        <div className="grid grid-cols-2 gap-4">
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

      <div className="mt-6 text-center text-sm text-gray-500">
        Already have an account?{' '}
        <Link to="/login" className="text-blue-600 font-semibold hover:underline">
          Sign In
        </Link>
      </div>
    </Card>
  );
};

export default Register;
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { toast } from 'react-hot-toast';
import { Sparkles, Github, Chrome, Mail, Lock } from 'lucide-react';
import Input from '../../components/ui/Input/Input';
import styles from './Login.module.css';

const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ email: '', password: '' });
  const [rememberMe, setRememberMe] = useState(true); // Defaulted to true as per description

  const mutation = useMutation({
    mutationFn: (data) => axios.post('http://localhost:8000/api/auth/login/', data),
    onSuccess: (response) => {
      localStorage.setItem('accessToken', response.data.access);
      toast.success('Welcome back!');
      navigate('/');
    },
    onError: (error) => {
      const msg = error.response?.data?.detail || 'Login failed';
      toast.error(msg);
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    mutation.mutate(formData);
  };

  return (
    <div className={styles.container}>
      {/* Left Panel - Violet-Cyan Gradient */}
      <div className={styles.leftPanel}>
        <div className={`${styles.decorationShape} ${styles.shape1}`} />
        <div className={`${styles.decorationShape} ${styles.shape2}`} />
        <div className={`${styles.decorationShape} ${styles.shape3}`} />
        
        <div className={styles.welcomeContent}>
          <div className={styles.brandLogoText}>
             CollabSpace AI <Sparkles size={24} className="text-yellow-300" fill="currentColor" />
          </div>
          <h1 className={styles.welcomeTitle}>
            Collaborate smarter with AI-powered workspace
          </h1>
        </div>
      </div>

      {/* Right Panel - Pale Lavender Background */}
      <div className={styles.rightPanel}>
        <div className={styles.loginCard}>
          
          <div className={styles.header}>
            <div className={styles.brandName}>
              CollabSpace AI <Sparkles size={16} className="text-yellow-500" fill="currentColor" />
            </div>
            <h2 className={styles.title}>Welcome back</h2>
          </div>

          <form className={styles.form} onSubmit={handleSubmit}>
            <div className={styles.inputWrapper}>
              <Input
                label="Email"
                type="email"
                placeholder="Enter your email"
                icon={Mail} // Using Icon prop
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
              />
            </div>
            
            <div className={styles.inputWrapper}>
              <Input
                label="Password"
                type="password"
                placeholder="Enter your password"
                icon={Lock} // Using Icon prop
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
              />
            </div>

            <div className={styles.actionsRow}>
              <label className={styles.checkboxLabel}>
                <input 
                  type="checkbox" 
                  className={styles.checkbox}
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                />
                Remember me
              </label>
            </div>

            <button 
              type="submit" 
              className={styles.signInBtn}
              disabled={mutation.isPending}
            >
              {mutation.isPending ? 'Signing in...' : 'Sign in →'}
            </button>
          </form>

          <div className={styles.divider}>
            <span>or</span>
          </div>

          <div className={styles.socialRow}>
            <button className={styles.socialBtn} onClick={() => toast.error("Google login not configured")}>
              <Chrome size={20} /> Google
            </button>
            <button className={styles.socialBtn} onClick={() => toast.error("GitHub login not configured")}>
              <Github size={20} /> GitHub
            </button>
          </div>

          <div className={styles.footer}>
            Don't have an account?
            <Link to="/register" className={styles.link}>
              Sign up
            </Link>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Login;
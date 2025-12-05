import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { toast } from 'react-hot-toast';
import { Sparkles, Github, Chrome, Mail, Lock, User } from 'lucide-react';
import Input from '../../components/ui/Input/Input';
import styles from './Register.module.css';

const Register = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [acceptedTerms, setAcceptedTerms] = useState(false);

  const mutation = useMutation({
    mutationFn: (data) => {
      const { confirmPassword, ...payload } = data;
      return axios.post('http://localhost:8000/api/auth/register/', payload);
    },
    onSuccess: () => {
      toast.success('Account created! Please log in.');
      navigate('/login');
    },
    onError: (error) => {
      const msg = error.response?.data?.detail || 'Registration failed';
      toast.error(msg);
    }
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    if (!acceptedTerms) {
      toast.error('Please accept the terms and conditions');
      return;
    }
    mutation.mutate(formData);
  };

  return (
    <div className={styles.container}>
      {/* Left Panel - Vivid Gradient & Shapes */}
      <div className={styles.leftPanel}>
        <div className={`${styles.decorationShape} ${styles.shape1}`} />
        <div className={`${styles.decorationShape} ${styles.shape2}`} />
        <div className={`${styles.decorationShape} ${styles.shape3}`} />
        
        <div className={styles.welcomeContent}>
          <div className={styles.brandLogoText}>
             CollabSpace AI <Sparkles size={24} className="text-yellow-300" fill="currentColor" />
          </div>
          <h1 className={styles.welcomeTitle}>
            Join the future of team collaboration
          </h1>
          <p className={styles.welcomeSub}>
            Create an account to unlock AI-powered tools, streamline workflows, and achieve more together.
          </p>
        </div>
      </div>

      {/* Right Panel - Floating Register Card */}
      <div className={styles.rightPanel}>
        <div className={styles.registerCard}>
          
          <div className={styles.header}>
            <div className={styles.brandName}>
              CollabSpace AI <Sparkles size={16} className="text-yellow-500" fill="currentColor" />
            </div>
            <h2 className={styles.title}>Create your account</h2>
          </div>

          <form className={styles.form} onSubmit={handleSubmit}>
            <div className={styles.inputWrapper}>
              <Input
                label="Full Name"
                type="text"
                placeholder="Jane Doe"
                icon={User}
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
                required
              />
            </div>

            <div className={styles.inputWrapper}>
              <Input
                label="Email"
                type="email"
                placeholder="jane@example.com"
                icon={Mail}
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                required
              />
            </div>
            
            <div className={styles.inputWrapper}>
              <Input
                label="Password"
                type="password"
                placeholder="Create a password"
                icon={Lock}
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                required
              />
            </div>

            <div className={styles.inputWrapper}>
              <Input
                label="Confirm Password"
                type="password"
                placeholder="Confirm your password"
                icon={Lock}
                value={formData.confirmPassword}
                onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                required
              />
            </div>

            <div className={styles.termsRow}>
              <input 
                type="checkbox" 
                id="terms"
                className={styles.checkbox}
                checked={acceptedTerms}
                onChange={(e) => setAcceptedTerms(e.target.checked)}
              />
              <label htmlFor="terms" className={styles.checkboxLabel}>
                I agree to the <Link to="/terms" className={styles.link}>Terms of Service</Link> and <Link to="/privacy" className={styles.link}>Privacy Policy</Link>.
              </label>
            </div>

            <button 
              type="submit" 
              className={styles.signUpBtn}
              disabled={mutation.isPending}
            >
              {mutation.isPending ? 'Creating account...' : 'Create account →'}
            </button>
          </form>

          <div className={styles.divider}>
            <span>or register with</span>
          </div>

          <div className={styles.socialRow}>
            <button className={styles.socialBtn} onClick={() => toast.error("Google registration not configured")}>
              <Chrome size={20} /> Google
            </button>
            <button className={styles.socialBtn} onClick={() => toast.error("GitHub registration not configured")}>
              <Github size={20} /> GitHub
            </button>
          </div>

          <div className={styles.footer}>
            Already have an account?
            <Link to="/login" className={styles.link}>
              Sign in
            </Link>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Register;
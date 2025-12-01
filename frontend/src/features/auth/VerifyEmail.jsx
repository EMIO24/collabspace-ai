import React, { useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import axios from 'axios';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';
import Card from '../../components/ui/Card/Card';
import Button from '../../components/ui/Button/Button';
import styles from '../../components/layouts/AuthLayout/AuthLayout.module.css';

const VerifyEmail = () => {
  const { key } = useParams(); // Assuming router is /verify-email/:key

  const mutation = useMutation({
    mutationFn: (data) => axios.post('http://localhost:8000/api/auth/verify-email/', data),
  });

  useEffect(() => {
    if (key) {
      mutation.mutate({ key });
    }
  }, [key]);

  const renderContent = () => {
    if (mutation.isPending) {
      return (
        <div className="flex flex-col items-center py-8">
          <Loader2 className="animate-spin text-blue-600 mb-4" size={48} />
          <p className="text-gray-600">Verifying your email address...</p>
        </div>
      );
    }

    if (mutation.isError) {
      return (
        <div className="text-center py-6">
          <div className="flex justify-center mb-4 text-red-500">
            <XCircle size={56} />
          </div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Verification Failed</h2>
          <p className="text-gray-500 mb-6">
            The verification link is invalid or has expired.
          </p>
          <Link to="/login">
            <Button variant="ghost">Return to Login</Button>
          </Link>
        </div>
      );
    }

    if (mutation.isSuccess) {
      return (
        <div className="text-center py-6">
          <div className="flex justify-center mb-4 text-emerald-500">
            <CheckCircle2 size={56} />
          </div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Email Verified!</h2>
          <p className="text-gray-500 mb-6">
            Your account has been successfully verified. You can now access the platform.
          </p>
          <Link to="/login">
            <Button className="w-full">Continue to Login</Button>
          </Link>
        </div>
      );
    }

    return null;
  };

  return (
    <Card className={styles.authCard}>
      {renderContent()}
    </Card>
  );
};

export default VerifyEmail;
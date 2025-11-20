import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

import Header from '@components/layout/Header';
import Login from '@pages/Auth/Login';
import Dashboard from '@pages/Dashboard/Dashboard';

const Loading = () => <div style={{ padding: 20 }}>Loading...</div>;

export default function App() {
  return (
    <div>
      <Header />
      <main className="container" style={{ paddingTop: 24 }}>
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            {/* add other routes here */}
          </Routes>
        </Suspense>
      </main>
    </div>
  );
}

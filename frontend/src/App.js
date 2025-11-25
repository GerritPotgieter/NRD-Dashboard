import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import DomainExplorer from './pages/DomainExplorer';
import DomainDetail from './pages/DomainDetail';
import PatternManagement from './pages/PatternManagement';
import WhitelistManagement from './pages/WhitelistManagement';
import WorkflowManagement from './pages/WorkflowManagement';
import Analytics from './pages/Analytics';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="domains" element={<DomainExplorer />} />
          <Route path="domains/:domain" element={<DomainDetail />} />
          <Route path="patterns" element={<PatternManagement />} />
          <Route path="whitelist" element={<WhitelistManagement />} />
          <Route path="workflow" element={<WorkflowManagement />} />
          {/* <Route path="analytics" element={<Analytics />} /> */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
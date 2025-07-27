import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import MainLayout from './components/MainLayout';
import ChatPage from './pages/ChatPage';
import MemoryPage from './pages/MemoryPage';
import StoragePage from './pages/StoragePage';
import SettingsPage from './pages/SettingsPage';
import './App.css';

const { Content } = Layout;

function App() {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <MainLayout>
          <Content style={{ padding: '24px', background: '#f0f2f5' }}>
            <Routes>
              <Route path="/" element={<ChatPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/memory" element={<MemoryPage />} />
              <Route path="/storage" element={<StoragePage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </Content>
        </MainLayout>
      </Layout>
    </Router>
  );
}

export default App; 
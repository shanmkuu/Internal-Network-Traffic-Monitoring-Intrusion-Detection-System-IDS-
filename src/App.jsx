import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import SecurityCommandCenter from './pages/security-command-center';
import NetworkAnalyticsHub from './pages/network-analytics-hub';
import SecurityAlertCenter from './pages/security-alert-center';
import LiveTrafficMonitor from './pages/live-traffic-monitor';
import Logs from './pages/system-logs';
import Reports from './pages/reports';
import Settings from './pages/settings';
import NotFound from './pages/NotFound';
import DashboardLayout from './components/layout/DashboardLayout';

function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <DashboardLayout>
                    <Routes>
                        <Route path="/" element={<SecurityCommandCenter />} />
                        <Route path="/live" element={<LiveTrafficMonitor />} />
                        <Route path="/alerts" element={<SecurityAlertCenter />} />
                        <Route path="/network" element={<NetworkAnalyticsHub />} />
                        <Route path="/logs" element={<Logs />} />
                        <Route path="/reports" element={<Reports />} />
                        <Route path="/settings" element={<Settings />} />
                        <Route path="*" element={<NotFound />} />
                    </Routes>
                </DashboardLayout>
            </AuthProvider>
        </BrowserRouter>
    );
}

export default App;

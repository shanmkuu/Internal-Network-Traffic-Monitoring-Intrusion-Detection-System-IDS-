import React from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import MobileBottomNav from '../ui/MobileBottomNav';

const DashboardLayout = ({ children }) => (
    <div style={{ background: 'var(--bg-deep)', minHeight: '100vh', color: 'var(--text-primary)', fontFamily: "'Space Grotesk', sans-serif" }}>
        {/* Animated ambient background */}
        <div className="aurora-bg" />
        {/* Moving scanline */}
        <div className="scanline" />

        {/* Sidebar */}
        <Sidebar />

        {/* Main content */}
        <main className="lg:pl-[220px] min-h-screen flex flex-col relative z-10">
            <Header />
            <div className="flex-1 p-5 lg:p-7">
                {children}
            </div>
        </main>

        {/* Mobile nav */}
        <div className="lg:hidden">
            <MobileBottomNav />
        </div>
    </div>
);

export default DashboardLayout;

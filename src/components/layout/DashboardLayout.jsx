import React from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import MobileBottomNav from '../ui/MobileBottomNav';

const DashboardLayout = ({ children }) => {
    return (
        <div className="min-h-screen bg-[#0F172A] text-gray-100 font-sans">
            {/* Desktop Sidebar */}
            <Sidebar />

            {/* Main Content Area */}
            <main className="lg:pl-64 min-h-screen relative flex flex-col">
                <Header />

                {/* Content Wrapper */}
                <div className="flex-1 p-6 lg:p-10">
                    {children}
                </div>
            </main>

            {/* Mobile Navigation (Hidden on Desktop) */}
            <div className="lg:hidden">
                <MobileBottomNav />
            </div>
        </div>
    );
};

export default DashboardLayout;

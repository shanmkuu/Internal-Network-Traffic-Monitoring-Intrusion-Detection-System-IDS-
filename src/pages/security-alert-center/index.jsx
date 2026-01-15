import React from 'react';
import AlertTable from './components/AlertTable';

const SecurityAlertCenter = () => {
    return (
        <div className="max-w-7xl mx-auto">
            <div className="mb-8">
                <h1 className="text-3xl font-mono font-bold text-white mb-2">Security Alert Center</h1>
                <p className="text-gray-400">Manage and investigate detected security incidents</p>
            </div>

            <div className="bg-[#1A2332] rounded-2xl border border-white/5 overflow-hidden">
                <AlertTable />
            </div>
        </div>
    );
};

export default SecurityAlertCenter;
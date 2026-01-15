import React from 'react';
import { BarChart2, Activity, Globe, Zap } from 'lucide-react';
import TrafficStats from './components/TrafficStats';
import GeographicThreatDistribution from './components/GeographicThreatDistribution';
import TopTalkersList from './components/TopTalkersList';
import ConnectedDevices from './components/ConnectedDevices';
import NetworkScanResults from './components/NetworkScanResults';

const NetworkAnalyticsHub = () => {
    return (
        <div className="max-w-7xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-mono font-bold text-white mb-2">Network Analytics Hub</h1>
                <p className="text-gray-400">Real-time network traffic analysis and statistics.</p>
            </div>

            {/* Real-time Stats from Backend */}
            <div className="bg-[#1A2332] rounded-2xl p-6 border border-white/5">
                <TrafficStats />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <GeographicThreatDistribution />
                <TopTalkersList />
            </div>

            {/* Connected Devices Module */}
            <ConnectedDevices />

            {/* Active Scan Results */}
            <NetworkScanResults />
        </div>
    );
};

export default NetworkAnalyticsHub;
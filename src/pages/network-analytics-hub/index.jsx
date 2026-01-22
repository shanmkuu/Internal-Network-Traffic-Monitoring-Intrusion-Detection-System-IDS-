import React from 'react';
import { BarChart2, Activity, Globe, Zap } from 'lucide-react';
import TrafficStats from './components/TrafficStats';
import TopTalkersList from './components/TopTalkersList';
import ConnectedDevices from './components/ConnectedDevices';
import NetworkScanResults from './components/NetworkScanResults';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/Tabs';

const NetworkAnalyticsHub = () => {
    return (
        <div className="max-w-7xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-mono font-bold text-white mb-2">Network Analytics Hub</h1>
                <p className="text-gray-400">Real-time network traffic analysis and statistics.</p>
            </div>

            <Tabs defaultValue="overview" className="w-full">
                <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
                    <TabsTrigger value="overview">Overview</TabsTrigger>
                    <TabsTrigger value="devices">Connected Devices</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-6">
                    {/* Real-time Stats from Backend */}
                    <div className="bg-[#1A2332] rounded-2xl p-6 border border-white/5">
                        <TrafficStats />
                    </div>

                    <div className="grid grid-cols-1 gap-6">
                        {/* Removed Geographic Threat Distribution as requested */}
                        <TopTalkersList />
                    </div>

                    {/* Active Scan Results */}
                    <NetworkScanResults />
                </TabsContent>

                <TabsContent value="devices">
                    {/* Connected Devices Module */}
                    <ConnectedDevices />
                </TabsContent>
            </Tabs>
        </div>
    );
};

export default NetworkAnalyticsHub;
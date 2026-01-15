import React, { useState, useEffect } from 'react';
import { Shield, Search, Terminal, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { api } from '../../../services/api';
import { format } from 'date-fns';

const NetworkScanResults = () => {
    const [results, setResults] = useState([]);
    const [scanning, setScanning] = useState(false);
    const [loading, setLoading] = useState(true);

    const fetchResults = async () => {
        try {
            const data = await api.getScanResults();
            setResults(data || []);
        } catch (error) {
            console.error("Failed to load scan results", error);
        } finally {
            setLoading(false);
        }
    };

    const handleStartScan = async () => {
        setScanning(true);
        try {
            // Trigger background scan
            await api.startScan();
            // In a real app, we might poll for status or wait. 
            // Here we'll just wait a bit and refresh, or let the user refresh.
            // But let's simulate a delay for improved UX since it's backgrounded.
            setTimeout(() => {
                fetchResults();
                setScanning(false);
            }, 2000);
        } catch (error) {
            console.error("Scan start failed", error);
            setScanning(false);
        }
    };

    useEffect(() => {
        fetchResults();
        const interval = setInterval(fetchResults, 10000); // Poll every 10s
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="bg-[#1E293B] rounded-xl border border-gray-700 p-6">
            <div className="flex justify-between items-center mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 backdrop-blur-sm shadow-inner shadow-indigo-500/10">
                        <Terminal className="w-5 h-5 text-indigo-400" />
                    </div>
                    <div>
                        <h3 className="text-white font-bold">Active Port Scan Reports</h3>
                        <p className="text-xs text-gray-500">Deep inspection of discovered hosts</p>
                    </div>
                </div>

                <button
                    onClick={handleStartScan}
                    disabled={scanning}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${scanning
                            ? 'bg-indigo-500/20 text-indigo-300 cursor-not-allowed'
                            : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-500/30'
                        }`}
                >
                    <Search className={`w-4 h-4 ${scanning ? 'animate-spin' : ''}`} />
                    {scanning ? 'Scanning Network...' : 'Start New Scan'}
                </button>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-gray-400">
                    <thead className="text-xs uppercase bg-[#0F172A] text-gray-500">
                        <tr>
                            <th className="px-4 py-3 rounded-l-lg">Time</th>
                            <th className="px-4 py-3">Host</th>
                            <th className="px-4 py-3">Open Ports</th>
                            <th className="px-4 py-3">Risk Level</th>
                            <th className="px-4 py-3 rounded-r-lg">Details</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                        {loading && results.length === 0 ? (
                            <tr><td colSpan="5" className="text-center py-8">Loading history...</td></tr>
                        ) : results.length === 0 ? (
                            <tr><td colSpan="5" className="text-center py-8 text-gray-500">No scan reports found. Start a scan to inspect the network.</td></tr>
                        ) : (
                            results.map((scan) => (
                                <tr key={scan.id} className="hover:bg-[#0F172A]/50 transition-colors group">
                                    <td className="px-4 py-3 font-mono text-xs">
                                        <div className="flex items-center gap-2">
                                            <Clock className="w-3 h-3 text-gray-600" />
                                            {format(new Date(scan.created_at), 'HH:mm:ss')}
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="text-white font-medium">{scan.ip_address}</div>
                                        <div className="text-xs text-gray-500 leading-none mt-0.5">{scan.hostname}</div>
                                    </td>
                                    <td className="px-4 py-3 font-mono text-xs text-indigo-300">
                                        {scan.open_ports ? scan.open_ports.split(',').map(p => (
                                            <span key={p} className="inline-block bg-indigo-500/10 px-1.5 py-0.5 rounded mr-1 border border-indigo-500/20">
                                                {p}
                                            </span>
                                        )) : <span className="text-gray-600">None detected</span>}
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className={`px-2 py-1 rounded-md text-xs font-bold border backdrop-blur-sm ${scan.risk_level === 'High' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                                scan.risk_level === 'Medium' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                                                    'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                            }`}>
                                            {scan.risk_level}
                                        </span>
                                    </td>
                                    <td className="px-4 py-3">
                                        <span className="text-xs bg-gray-800 px-2 py-1 rounded text-gray-400 group-hover:bg-gray-700 transition-colors">
                                            {scan.scan_type}
                                        </span>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default NetworkScanResults;

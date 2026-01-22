import React, { useState, useEffect } from 'react';
import { Shield, Search, Terminal, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { api } from '../../../services/api';
import { format } from 'date-fns';

const NetworkScanResults = () => {
    const [results, setResults] = useState([]);
    const [scanning, setScanning] = useState(false);
    const [loading, setLoading] = useState(true);
    const [expandedRows, setExpandedRows] = useState(new Set());

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
            await api.startScan();
            setTimeout(() => {
                fetchResults();
                setScanning(false);
            }, 2000);
        } catch (error) {
            console.error("Scan start failed", error);
            setScanning(false);
        }
    };

    const toggleRow = (id) => {
        const newExpanded = new Set(expandedRows);
        if (newExpanded.has(id)) {
            newExpanded.delete(id);
        } else {
            newExpanded.add(id);
        }
        setExpandedRows(newExpanded);
    };

    useEffect(() => {
        fetchResults();
        const interval = setInterval(fetchResults, 10000);
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
                            <th className="px-4 py-3">Host / OS</th>
                            <th className="px-4 py-3">Open Ports</th>
                            <th className="px-4 py-3">Risk Level</th>
                            <th className="px-4 py-3 rounded-r-lg">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                        {loading && results.length === 0 ? (
                            <tr><td colSpan="5" className="text-center py-8">Loading history...</td></tr>
                        ) : results.length === 0 ? (
                            <tr><td colSpan="5" className="text-center py-8 text-gray-500">No scan reports found. Start a scan to inspect the network.</td></tr>
                        ) : (
                            results.map((scan) => (
                                <React.Fragment key={scan.id}>
                                    <tr className={`hover:bg-[#0F172A]/50 transition-colors group cursor-pointer ${expandedRows.has(scan.id) ? 'bg-[#0F172A]/30' : ''}`} onClick={() => toggleRow(scan.id)}>
                                        <td className="px-4 py-3 font-mono text-xs">
                                            <div className="flex items-center gap-2">
                                                <Clock className="w-3 h-3 text-gray-600" />
                                                {format(new Date(scan.created_at), 'HH:mm:ss')}
                                            </div>
                                        </td>
                                        <td className="px-4 py-3">
                                            <div className="text-white font-medium">{scan.ip_address}</div>
                                            <div className="text-xs text-gray-500 leading-none mt-1">{scan.hostname}</div>
                                            {scan.os_details && scan.os_details !== 'Unknown' && (
                                                <div className="text-[10px] text-blue-400 mt-1 font-mono">{scan.os_details}</div>
                                            )}
                                        </td>
                                        <td className="px-4 py-3 font-mono text-xs text-indigo-300">
                                            {scan.open_ports ? scan.open_ports.split(',').map(p => (
                                                <span key={p} className="inline-block bg-indigo-500/10 px-1.5 py-0.5 rounded mr-1 border border-indigo-500/20">
                                                    {p.split(':')[0]}
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
                                        <td className="px-4 py-3 text-right">
                                            <button className="text-gray-400 hover:text-white transition-colors">
                                                {expandedRows.has(scan.id) ? 'Collapse' : 'Details'}
                                            </button>
                                        </td>
                                    </tr>
                                    {expandedRows.has(scan.id) && (
                                        <tr>
                                            <td colSpan="5" className="px-4 py-4 bg-[#0F172A]/30 border-t border-gray-700/50">
                                                <div className="space-y-4">
                                                    {/* Full Port Details */}
                                                    <div>
                                                        <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Service Detection</h4>
                                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                                            {scan.open_ports ? scan.open_ports.split(',').map((p, idx) => {
                                                                const [port, ...details] = p.split(':');
                                                                const serviceInfo = details.join(':').trim();
                                                                return (
                                                                    <div key={idx} className="bg-black/20 p-2 rounded border border-gray-700/50 font-mono text-xs text-indigo-300 flex flex-col">
                                                                        <span className="font-bold text-white">Port {port}</span>
                                                                        <span className="text-indigo-200/70 text-[10px] break-words">
                                                                            {serviceInfo || 'No banner available'}
                                                                        </span>
                                                                    </div>
                                                                );
                                                            }) : <span className="text-gray-500 text-sm">No open ports</span>}
                                                        </div>
                                                    </div>

                                                    {/* Vulnerabilities */}
                                                    {scan.vulnerabilities && scan.vulnerabilities.length > 0 && (
                                                        <div>
                                                            <h4 className="text-xs font-bold text-red-400 uppercase mb-2 flex items-center gap-2">
                                                                <AlertTriangle className="w-3 h-3" /> Vulnerabilities Found
                                                            </h4>
                                                            <div className="space-y-2">
                                                                {scan.vulnerabilities.map((vuln, vIdx) => (
                                                                    <div key={vIdx} className="bg-red-900/10 p-3 rounded border border-red-500/10">
                                                                        <div className="flex justify-between mb-1">
                                                                            <span className="text-red-300 font-bold text-xs">{vuln.script}</span>
                                                                            <span className="text-gray-500 text-[10px]">{vuln.port ? `Port ${vuln.port}` : 'Host Script'}</span>
                                                                        </div>
                                                                        <pre className="text-[10px] text-gray-400 whitespace-pre-wrap font-mono">{vuln.output}</pre>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    )}

                                                    {(!scan.vulnerabilities || scan.vulnerabilities.length === 0) && (
                                                        <div className="flex items-center gap-2 text-emerald-500/50 text-xs">
                                                            <CheckCircle className="w-3 h-3" /> No obvious vulnerabilities detected by scripts.
                                                        </div>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
export default NetworkScanResults;

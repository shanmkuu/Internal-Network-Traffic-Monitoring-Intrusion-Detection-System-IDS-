import React, { useState, useEffect, useRef } from 'react';
import { Wifi, Server, Activity, AlertTriangle, Monitor, Database } from 'lucide-react';
import { api } from '../../services/api';
import CyberGraph3D from './components/CyberGraph3D';
import ThreatProfile from './components/ThreatProfile';

const CyberCommandVisualizer = () => {
    const [wazuhPayload, setWazuhPayload] = useState(null);
    const [selectedNode, setSelectedNode] = useState(null);
    const [isRunning, setIsRunning] = useState(true);
    const [isOffline, setIsOffline] = useState(false);

    // Auto-resize canvas container
    const containerRef = useRef(null);
    const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

    useEffect(() => {
        const handleResize = () => {
            if (containerRef.current) {
                setDimensions({
                    width: containerRef.current.clientWidth,
                    height: containerRef.current.clientHeight
                });
            }
        };
        window.addEventListener('resize', handleResize);
        handleResize();
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const [isSimulationMode, setIsSimulationMode] = useState(false);
    const [usingLocalFallback, setUsingLocalFallback] = useState(false);

    // Maps the local (PyShark/Scapy) Monitor alerts to the Wazuh Payload format
    const mapLocalAlertsToWazuhFormat = (localAlerts) => {
        const mappedAlerts = localAlerts.map(a => {
            const level = a.alert.severity === 1 ? 12 : a.alert.severity === 2 ? 8 : 4;
            return {
                source_ip: a.src_ip,
                rule: { level: level, description: a.alert.signature },
                threat: { tactic: a.alert.category || 'Local Sniffer Detection' },
                agent: { id: 'local' }
            };
        });

        const ipGroups = {};
        mappedAlerts.forEach(a => {
            if (!ipGroups[a.source_ip]) ipGroups[a.source_ip] = { count: 0, peak_level: 0, tactics: new Set(), raw: a };
            ipGroups[a.source_ip].count += 1;
            if (a.rule.level > ipGroups[a.source_ip].peak_level) ipGroups[a.source_ip].peak_level = a.rule.level;
            ipGroups[a.source_ip].tactics.add(a.threat.tactic);
        });

        const incidents = [];
        const looseAlerts = [];

        Object.entries(ipGroups).forEach(([ip, data]) => {
            if (data.count > 1) {
                incidents.push({
                    source_ip: ip,
                    count: data.count,
                    peak_level: data.peak_level,
                    tactics: Array.from(data.tactics),
                    agent_ids: ['local-monitor']
                });
            } else {
                looseAlerts.push(data.raw);
            }
        });

        return {
            summary: {
                total: mappedAlerts.length,
                critical: mappedAlerts.filter(a => a.rule.level >= 12).length,
                incidents: incidents.length
            },
            incidents: incidents,
            alerts: looseAlerts
        };
    };

    // Mock data generator for simulation mode
    const generateMockWazuhPayload = () => {
        const randomIP = () => `${Math.floor(Math.random() * 200) + 10}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`;

        return {
            summary: {
                total: Math.floor(Math.random() * 1500) + 300,
                critical: Math.floor(Math.random() * 45) + 5,
                incidents: Math.floor(Math.random() * 8) + 2
            },
            incidents: [
                { source_ip: '192.168.1.105', count: Math.floor(Math.random() * 200) + 50, peak_level: 15, tactics: ['Execution', 'Privilege Escalation'] },
                { source_ip: '8.8.8.8', count: Math.floor(Math.random() * 100) + 20, peak_level: 12, tactics: ['Credential Access'] },
                { source_ip: randomIP(), count: Math.floor(Math.random() * 40) + 10, peak_level: 10, tactics: ['Lateral Movement'] }
            ],
            alerts: Array.from({ length: 5 }).map(() => ({
                source_ip: randomIP(),
                rule: { level: Math.floor(Math.random() * 5) + 6 },
                threat: { tactic: ['Discovery', 'Reconnaissance', 'Initial Access'][Math.floor(Math.random() * 3)] }
            }))
        };
    };

    // Polling Logic
    const fetchData = async () => {
        if (!isRunning) return;

        if (isSimulationMode) {
            setWazuhPayload(generateMockWazuhPayload());
            setIsOffline(false);
            return;
        }

        try {
            // Poll for last 6 hours of high/critical alerts
            let data = await api.getWazuhAlerts('6h');

            // Check if backend returned empty shell (implies Wazuh offline or no data)
            if (!data || !data.summary || Object.keys(data.summary).length === 0) {
                // Fallback to local monitor.py alerts
                const localAlerts = await api.getAlerts();
                if (localAlerts && localAlerts.length > 0) {
                    data = mapLocalAlertsToWazuhFormat(localAlerts);
                    setUsingLocalFallback(true);
                    setIsOffline(false);
                } else {
                    setUsingLocalFallback(false);
                    setIsOffline(true);
                    return;
                }
            } else {
                setUsingLocalFallback(false);
                setIsOffline(false);
            }

            setWazuhPayload(data);

            // If a node is selected, update its data if new alerts came in
            if (selectedNode) {
                const latestIncidents = data.incidents || [];
                const latestAlerts = data.alerts || [];

                const updatedNodeRaw =
                    latestIncidents.find(i => i.source_ip === selectedNode.id) ||
                    latestAlerts.find(a => a.source_ip === selectedNode.id);

                if (updatedNodeRaw) {
                    setSelectedNode(prev => ({
                        ...prev,
                        count: updatedNodeRaw.count || 1,
                        peakLevel: updatedNodeRaw.peak_level || updatedNodeRaw.rule?.level || prev.peakLevel
                    }));
                }
            }
        } catch (error) {
            console.error("Failed to fetch graph data", error);
            setIsOffline(true);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 4000); // Poll every 4 seconds
        return () => clearInterval(interval);
    }, [isRunning, isSimulationMode]);

    const handleNodeClick = (node) => {
        // Only select Attacker nodes
        if (node.group === 'attacker') {
            setSelectedNode(node);
        } else {
            setSelectedNode(null);
        }
    };

    // Calculate dynamic UI summaries based on payload
    const summary = wazuhPayload?.summary || { total: 0, critical: 0, incidents: 0 };

    return (
        <div className="flex flex-col h-full space-y-4" style={{ minHeight: 'calc(100vh - 8rem)' }}>

            {/* Header */}
            <div className="flex items-center justify-between shrink-0">
                <div>
                    <h1 className="text-xl font-bold font-mono tracking-tight" style={{ color: '#F8FAFC' }}>
                        PROACTIVE CYBER INTELLIGENCE
                    </h1>
                    <p className="text-xs mt-0.5 tracking-wider uppercase font-semibold" style={{ color: '#94A3B8' }}>
                        Global Threat Landscape & Neural Attack Graph
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    {usingLocalFallback && !isSimulationMode && (
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-amber-500/30 bg-amber-500/10 backdrop-blur">
                            <Wifi className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
                            <span className="text-xs font-mono font-bold text-amber-300">
                                LOCAL SENSOR FALLBACK
                            </span>
                        </div>
                    )}
                    {isSimulationMode && (
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-indigo-500/30 bg-indigo-500/10 backdrop-blur">
                            <Activity className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
                            <span className="text-xs font-mono font-bold text-indigo-300">
                                SIMULATION ACTIVE
                            </span>
                        </div>
                    )}
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-md border border-white/10 bg-white/5">
                        <Activity className={`w-3.5 h-3.5 ${!isOffline && isRunning ? 'text-emerald-400 animate-pulse' : 'text-red-400'}`} />
                        <span className="text-xs font-mono font-bold text-gray-300">
                            {isOffline ? 'WAZUH OFFLINE' : isRunning ? 'ACTIVE UPLINK' : 'PAUSED'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Main Visualizer Stage */}
            <div className="relative flex-1 rounded-xl overflow-hidden border border-indigo-900/50 shadow-2xl bg-[#0A0F1C]" ref={containerRef}>

                {/* 3D Force Graph */}
                <CyberGraph3D
                    width={dimensions.width}
                    height={dimensions.height}
                    wazuhPayload={wazuhPayload}
                    onNodeClick={handleNodeClick}
                />

                {/* Top Left Stats HUD overlay */}
                <div className="absolute top-4 left-4 flex flex-col gap-3 pointer-events-none">

                    <div className="flex items-center gap-3 bg-slate-900/60 backdrop-blur-md px-4 py-2 rounded-lg border border-slate-700/50 shadow-lg">
                        <div className="p-1.5 bg-indigo-500/20 rounded text-indigo-400"><Database className="w-4 h-4" /></div>
                        <div>
                            <div className="text-[10px] text-gray-400 uppercase font-bold tracking-widest leading-tight">Total Assaults</div>
                            <div className="text-lg font-mono font-bold text-white leading-none mt-0.5">{summary.total}</div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3 bg-slate-900/60 backdrop-blur-md px-4 py-2 rounded-lg border border-slate-700/50 shadow-lg">
                        <div className="p-1.5 bg-red-500/20 rounded text-red-400"><AlertTriangle className="w-4 h-4" /></div>
                        <div>
                            <div className="text-[10px] text-gray-400 uppercase font-bold tracking-widest leading-tight">Critical Threats</div>
                            <div className="text-lg font-mono font-bold text-white leading-none mt-0.5">{summary.critical}</div>
                        </div>
                    </div>

                    <div className="flex items-center gap-3 bg-slate-900/60 backdrop-blur-md px-4 py-2 rounded-lg border border-slate-700/50 shadow-lg">
                        <div className="p-1.5 bg-amber-500/20 rounded text-amber-400"><Monitor className="w-4 h-4" /></div>
                        <div>
                            <div className="text-[10px] text-gray-400 uppercase font-bold tracking-widest leading-tight">Active Incidents</div>
                            <div className="text-lg font-mono font-bold text-white leading-none mt-0.5">{summary.incidents}</div>
                        </div>
                    </div>

                </div>

                {/* Threat Profile Panel Overlay (Right side) */}
                <ThreatProfile
                    node={selectedNode}
                    onClose={() => setSelectedNode(null)}
                />

                {/* Bottom Status Bar */}
                <div className="absolute bottom-0 inset-x-0 h-8 bg-black/40 backdrop-blur border-t border-indigo-900/50 flex items-center justify-between px-4">
                    <div className="flex items-center gap-4 text-[10px] font-mono font-semibold tracking-widest text-indigo-300">
                        <span className="flex items-center gap-1.5"><Server className="w-3 h-3" /> CORE DEPLOYED</span>
                        <span className="flex items-center gap-1.5"><Wifi className="w-3 h-3" /> ORCHESTRATOR ONLINE</span>
                    </div>
                    <div className="text-[10px] text-gray-500 font-mono">
                        DRAG TO ROTATE | SCROLL TO ZOOM | CLICK NODE TO INSPECT
                    </div>
                </div>

                {/* Offline Warning Banner */}
                {isOffline && !isSimulationMode && (
                    <div className="absolute inset-x-0 top-1/2 -translate-y-1/2 flex flex-col items-center justify-center p-8 bg-red-950/80 backdrop-blur-sm border-y border-red-500/30">
                        <AlertTriangle className="w-12 h-12 text-red-500 mb-3 animate-pulse" />
                        <h2 className="text-2xl font-bold font-mono text-white mb-2 tracking-widest">UPLINK SEVERED</h2>
                        <p className="text-red-200 font-mono text-sm max-w-md text-center mb-6">
                            The Wazuh Manager is offline or unreachable. Proactive Intelligence Visualizer requires a live event stream.
                        </p>
                        <button
                            onClick={() => { setIsSimulationMode(true); setIsOffline(false); setIsRunning(true); fetchData(); }}
                            className="px-6 py-2.5 bg-red-500/20 hover:bg-red-500/30 text-red-300 font-mono font-bold tracking-widest text-xs border border-red-500/50 rounded transition-all"
                        >
                            INITIALIZE SIMULATION
                        </button>
                    </div>
                )}
            </div>

        </div>
    );
};

export default CyberCommandVisualizer;
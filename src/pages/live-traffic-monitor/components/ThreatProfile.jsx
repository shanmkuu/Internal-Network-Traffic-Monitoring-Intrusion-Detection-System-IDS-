import React, { useState } from 'react';
import { ShieldAlert, Crosshair, Server, Eye, Zap, Shield, AlertTriangle } from 'lucide-react';
import { api } from '../../../services/api';

const ThreatProfile = ({ node, onClose }) => {
    const [isBlocking, setIsBlocking] = useState(false);
    const [blockSuccess, setBlockSuccess] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');

    if (!node || node.group === 'core') return null;

    const riskColor = node.peakLevel >= 12 ? '#DC2626' : node.peakLevel >= 7 ? '#F59E0B' : '#818CF8';
    const riskLabel = node.peakLevel >= 12 ? 'CRITICAL' : node.peakLevel >= 7 ? 'HIGH' : 'ELEVATED';

    const handleActiveResponse = async () => {
        setIsBlocking(true);
        setErrorMsg('');
        try {
            // Attempt to block via the Wazuh middleware
            // Assuming the attacker targets agent '001'. In a real setup, infer from node.raw.agent.id
            const agentId = node.raw?.agent_ids?.[0] || node.raw?.agent?.id || '001';
            const res = await api.blockIpOnWazuh(node.id, agentId);

            if (res.error || res.detail) {
                setErrorMsg(res.error || res.detail || 'Failed to trigger response');
            } else if (res.status === 'already_mitigated') {
                setBlockSuccess(true);
                setErrorMsg('IP is already actively blocked.');
            } else {
                setBlockSuccess(true);
            }
        } catch (err) {
            setErrorMsg('Network error triggering response.');
        } finally {
            setIsBlocking(false);
        }
    };

    return (
        <div className="absolute top-4 right-4 w-80 rounded-xl overflow-hidden shadow-2xl transition-all duration-300 transform translate-x-0"
            style={{
                background: 'rgba(15, 23, 42, 0.85)',
                backdropFilter: 'blur(16px)',
                border: `1px solid ${riskColor}50`,
                boxShadow: `0 0 30px ${riskColor}15`
            }}>

            {/* Header */}
            <div className="p-4 border-b flex justify-between items-start" style={{ borderColor: 'rgba(255,255,255,0.05)' }}>
                <div>
                    <div className="text-[10px] font-bold tracking-widest uppercase flex items-center gap-1.5" style={{ color: riskColor }}>
                        <ShieldAlert className="w-3 h-3" />
                        Target Locked
                    </div>
                    <h3 className="text-xl font-mono mt-1 text-white">{node.id}</h3>
                    <p className="text-xs text-gray-400 mt-0.5">External Entity</p>
                </div>
                <button onClick={onClose} className="p-1.5 hover:bg-white/5 rounded-md text-gray-400">
                    <Crosshair className="w-4 h-4" />
                </button>
            </div>

            {/* Content body */}
            <div className="p-5 space-y-5">

                {/* Threat Telemetry */}
                <div className="space-y-3">
                    <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-400 flex items-center gap-2"><Zap className="w-3.5 h-3.5" /> Intensity</span>
                        <span className="font-mono font-semibold" style={{ color: riskColor }}>{riskLabel} L{node.peakLevel}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-400 flex items-center gap-2"><Target className="w-3.5 h-3.5" /> Tactic</span>
                        <span className="text-white font-medium">{node.tactic}</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                        <span className="text-gray-400 flex items-center gap-2"><Eye className="w-3.5 h-3.5" /> Detections</span>
                        <span className="text-white font-mono">{node.count} events</span>
                    </div>
                    {node.isIncident && (
                        <div className="flex justify-between items-center text-sm">
                            <span className="text-gray-400 flex items-center gap-2"><Server className="w-3.5 h-3.5" /> Grouping</span>
                            <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">
                                Correlated Incident
                            </span>
                        </div>
                    )}
                </div>

                {/* Glitch WARNING for Level 15 */}
                {node.peakLevel >= 15 && (
                    <div className="p-3 rounded bg-red-500/10 border border-red-500/30">
                        <div className="flex items-start gap-2 text-red-400 text-xs font-mono">
                            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                            <p>CRITICAL ASSAULT DETECTED. The orchestrator may have already initiated automated response protocols.</p>
                        </div>
                    </div>
                )}

                {/* Active Response Button */}
                <div className="pt-2 border-t border-white/5">
                    {blockSuccess ? (
                        <div className="w-full py-2.5 px-4 rounded-md flex items-center justify-center gap-2 text-sm font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                            <Shield className="w-4 h-4" />
                            Threat Neutralized
                        </div>
                    ) : (
                        <button
                            disabled={isBlocking}
                            onClick={handleActiveResponse}
                            className="w-full py-2.5 px-4 rounded-md flex items-center justify-center gap-2 text-sm font-bold transition-all relative overflow-hidden group"
                            style={{
                                background: isBlocking ? 'rgba(79,70,229,0.5)' : '#4F46E5',
                                color: 'white'
                            }}
                        >
                            {isBlocking ? (
                                <span className="animate-pulse">Deploying Protocol...</span>
                            ) : (
                                <>
                                    <ShieldAlert className="w-4 h-4" />
                                    Trigger Active Response
                                </>
                            )}
                            {/* Hover shine effect */}
                            <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent group-hover:animate-[shimmer_1.5s_infinite]" />
                        </button>
                    )}

                    {errorMsg && (
                        <div className="mt-2 text-xs text-red-400 text-center bg-red-500/10 p-2 rounded">
                            {errorMsg}
                        </div>
                    )}
                </div>

            </div>
        </div>
    );
};

// Quick helper icon for Tactic row
const Target = ({ className }) => (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="6" /><circle cx="12" cy="12" r="2" />
    </svg>
);

export default ThreatProfile;

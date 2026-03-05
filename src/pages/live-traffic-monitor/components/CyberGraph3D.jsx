import React, { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import * as THREE from 'three';

/**
 * Maps the backend Wazuh Bento Box payload into D3 graph data.
 * The graph consists of one central "Core" node, and surrounding
 * Attacker nodes based on Security Incidents and raw alerts.
 */
const buildGraphData = (wazuhPayload) => {
    const nodes = [];
    const links = [];

    // Node 0: The Core (Internal Network)
    nodes.push({
        id: 'CORE',
        label: 'Internal Network',
        group: 'core',
        val: 10, // Size
        color: '#10B981', // Emerald/Teal
        glowColor: '#34D399',
    });

    if (!wazuhPayload) return { nodes, links };

    const { alerts = [], incidents = [] } = wazuhPayload;

    // Helper to add a threat node and a link to CORE
    const addThreatNode = (ip, data, isIncident) => {
        // Prevent duplicate nodes
        if (nodes.find(n => n.id === ip)) return;

        // Determine color based on highest severity
        let color = '#818CF8'; // default blue-ish (info)
        const peakLevel = isIncident ? data.peak_level : data.rule?.level;

        if (peakLevel >= 12) color = '#DC2626'; // Crimson
        else if (peakLevel >= 7) color = '#F59E0B'; // Amber

        // Map Tactic
        let tactic = 'Unknown';
        if (isIncident && data.tactics && data.tactics.length > 0) tactic = data.tactics[0];
        else if (!isIncident && data.threat?.tactic) tactic = data.threat.tactic;

        nodes.push({
            id: ip,
            label: ip,
            group: 'attacker',
            val: isIncident ? Math.min(data.count * 1.5, 8) : 3, // Base size on alert volume
            color: color,
            tactic: tactic,
            peakLevel: peakLevel,
            count: isIncident ? data.count : 1,
            isIncident: isIncident,
            raw: data // Keep original data for the Threat Profile
        });

        // Link Attacker -> Core
        links.push({
            source: ip,
            target: 'CORE',
            color: color + '60', // semi-transparent
            particleWidth: isIncident ? 2 : 1,
        });
    };

    // 1. Map Correlated Incidents (Highest Priority)
    incidents.forEach(inc => {
        if (inc.source_ip) addThreatNode(inc.source_ip, inc, true);
    });

    // 2. Map loose Alerts (Only if they have an IP and aren't already grouped)
    alerts.forEach(al => {
        if (al.source_ip) addThreatNode(al.source_ip, al, false);
    });

    return { nodes, links };
};

const CyberGraph3D = ({ wazuhPayload, onNodeClick, width, height }) => {
    const fgRef = useRef();
    const [graphData, setGraphData] = useState({ nodes: [{ id: 'CORE', group: 'core' }], links: [] });

    // Rebuild graph data when payload updates
    useEffect(() => {
        setGraphData(buildGraphData(wazuhPayload));
    }, [wazuhPayload]);

    // Initial camera positioning
    useEffect(() => {
        if (fgRef.current) {
            fgRef.current.cameraPosition({ z: 300 }); // Pull camera back
        }
    }, []);

    // Custom Node Rendering (Glowing spheres via Three.js)
    const nodeThreeObject = useCallback((node) => {
        if (node.group === 'core') {
            const material = new THREE.MeshPhongMaterial({
                color: node.color,
                emissive: node.glowColor,
                emissiveIntensity: 0.8,
                shininess: 100,
                transparent: true,
                opacity: 0.9,
            });
            return new THREE.Mesh(new THREE.SphereGeometry(node.val, 32, 32), material);
        } else {
            // Attacker nodes
            const material = new THREE.MeshLambertMaterial({
                color: node.color,
                transparent: true,
                opacity: 0.8,
            });
            return new THREE.Mesh(new THREE.SphereGeometry(node.val, 16, 16), material);
        }
    }, []);

    return (
        <div className="absolute inset-0 overflow-hidden" style={{ background: '#0A0F1C' }}>
            <ForceGraph3D
                ref={fgRef}
                width={width}
                height={height}
                graphData={graphData}
                nodeThreeObject={nodeThreeObject}
                backgroundColor="#0A0F1C"
                showNavInfo={false}
                // Link styling
                linkColor="color"
                linkWidth={1}
                linkOpacity={0.4}
                // Particle animation for active threats
                linkDirectionalParticles={(link) => (link.particleWidth > 1 ? 4 : 1)}
                linkDirectionalParticleWidth="particleWidth"
                linkDirectionalParticleSpeed={0.005}
                linkDirectionalParticleColor="color"
                // Interaction
                onNodeClick={onNodeClick}
                onNodeHover={(node) => {
                    document.body.style.cursor = node ? 'pointer' : 'default';
                }}
            />
            {/* Ambient Lighting so lambda materials show */}
            <ambientLight intensity={0.5} color="#ffffff" />
            <directionalLight position={[0, 100, 100]} intensity={0.8} />
        </div>
    );
};

export default CyberGraph3D;

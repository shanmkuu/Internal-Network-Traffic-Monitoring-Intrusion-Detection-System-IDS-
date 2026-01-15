import React from 'react';
import { Link } from 'react-router-dom';

const NotFound = () => {
    return (
        <div className="h-full flex items-center justify-center">
            <div className="text-center p-8 bg-[#1A2332] rounded-2xl border border-white/5 shadow-2xl max-w-md w-full">
                <h1 className="text-8xl font-mono font-bold text-blue-500 mb-4 opacity-50">404</h1>
                <h2 className="text-2xl font-bold text-white mb-2">Page Not Found</h2>
                <p className="text-gray-400 mb-8">The route you requested does not exist in the security map.</p>
                <Link to="/" className="inline-flex items-center justify-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl transition-colors w-full">
                    Return to Command Center
                </Link>
            </div>
        </div>
    );
};

export default NotFound;

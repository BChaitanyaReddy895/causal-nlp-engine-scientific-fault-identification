// History component to track previous verifications
import React, { useState, useEffect } from 'react';

export const VerificationHistory = ({ onSelectClaim }) => {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    // Load from localStorage
    const saved = localStorage.getItem('verification_history');
    if (saved) setHistory(JSON.parse(saved));
  }, []);

  const saveToHistory = (claim, result) => {
    const entry = {
      id: Date.now(),
      claim,
      verdict: result.verdict,
      confidence: result.confidence,
      timestamp: new Date().toISOString()
    };
    const newHistory = [entry, ...history].slice(0, 50);
    setHistory(newHistory);
    localStorage.setItem('verification_history', JSON.stringify(newHistory));
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h2 className="font-bold text-lg mb-4">Recent Verifications</h2>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {history.map(item => (
          <div
            key={item.id}
            onClick={() => onSelectClaim(item.claim)}
            className="p-3 hover:bg-gray-100 cursor-pointer border-l-4 border-blue-500"
          >
            <p className="text-sm truncate">{item.claim}</p>
            <p className="text-xs text-gray-600">{item.verdict} ({(item.confidence * 100).toFixed(0)}%)</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default VerificationHistory;

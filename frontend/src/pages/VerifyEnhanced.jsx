// Enhanced verification page with evidence display and graph visualization

import React, { useState } from 'react';
import axios from 'axios';
import GraphVisualization from './GraphVisualization';

export const VerifyPage = () => {
  const [claim, setClaim] = useState('');
  const [domain, setDomain] = useState('medicine');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleVerify = async () => {
    if (!claim.trim()) return;
    setLoading(true);
    try {
      const response = await axios.post('/api/verify', { claim, domain });
      setResult(response.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const verdictColors = {
    'SUPPORTS_CAUSALITY': 'bg-green-100 text-green-800',
    'REFUTES_CAUSALITY': 'bg-red-100 text-red-800',
    'CORRELATION_NOT_CAUSAL': 'bg-yellow-100 text-yellow-800',
    'UNVERIFIABLE': 'bg-gray-100 text-gray-800',
    'MISSING_MECHANISM': 'bg-blue-100 text-blue-800'
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Verify Scientific Claims</h1>
        <p className="text-gray-600 mb-8">Analyze causal relationships in scientific claims</p>

        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <textarea
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
            placeholder="Enter a scientific claim to verify..."
            className="w-full h-24 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <div className="mt-4 flex gap-4">
            <select
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg"
            >
              <option value="medicine">Medicine</option>
              <option value="biology">Biology</option>
              <option value="nutrition">Nutrition</option>
              <option value="psychology">Psychology</option>
            </select>
            <button
              onClick={handleVerify}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
            >
              {loading ? 'Verifying...' : 'Verify Claim'}
            </button>
          </div>
        </div>

        {result && (
          <div className="space-y-6">
            {/* Verdict Card */}
            <div className="bg-white rounded-lg shadow-lg p-8">
              <div className={`inline-block px-4 py-2 rounded-full font-bold ${verdictColors[result.verdict]}`}>
                {result.verdict}
              </div>
              <p className="text-2xl font-bold text-gray-900 mt-4">Confidence: {(result.confidence * 100).toFixed(1)}%</p>
              <p className="text-gray-700 mt-2">{result.explanation}</p>
            </div>

            {/* Causal Graph */}
            {result.causal_graph && (
              <div className="bg-white rounded-lg shadow-lg p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Causal Graph</h2>
                <GraphVisualization
                  nodes={result.causal_graph.nodes}
                  edges={result.causal_graph.edges}
                />
              </div>
            )}

            {/* Evidence */}
            {result.evidence.length > 0 && (
              <div className="bg-white rounded-lg shadow-lg p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Supporting Evidence</h2>
                <div className="space-y-4">
                  {result.evidence.map((ev, idx) => (
                    <div key={idx} className="border-l-4 border-blue-500 pl-4 py-2">
                      <p className="font-semibold">{ev.title}</p>
                      <p className="text-gray-600 text-sm">{ev.snippet}</p>
                      <a href={ev.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                        View paper →
                      </a>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Missing Mechanisms */}
            {result.missing_mechanism.length > 0 && (
              <div className="bg-orange-50 border-l-4 border-orange-400 p-6 rounded">
                <h3 className="font-bold text-orange-900 mb-2">Missing Mechanistic Information</h3>
                <ul className="list-disc list-inside text-orange-800">
                  {result.missing_mechanism.map((m, i) => (
                    <li key={i}>{m}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default VerifyPage;

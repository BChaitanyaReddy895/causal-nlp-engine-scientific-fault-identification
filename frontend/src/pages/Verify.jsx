import React, { useState } from 'react';
import axios from 'axios';
import { FaSpinner } from 'react-icons/fa';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function Verify() {
  const [claim, setClaim] = useState('');
  const [domain, setDomain] = useState('medicine');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!claim.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(`${API_URL}/api/verify`, {
        claim,
        domain,
      });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.message || 'Verification failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getVerdictColor = (verdict) => {
    switch (verdict) {
      case 'SUPPORTS_CAUSALITY':
        return 'bg-green-500/20 border-green-500/50 text-green-200';
      case 'REFUTES_CAUSALITY':
        return 'bg-red-500/20 border-red-500/50 text-red-200';
      case 'CORRELATION_NOT_CAUSAL':
        return 'bg-yellow-500/20 border-yellow-500/50 text-yellow-200';
      case 'UNVERIFIABLE':
        return 'bg-gray-500/20 border-gray-500/50 text-gray-200';
      default:
        return 'bg-purple-500/20 border-purple-500/50 text-purple-200';
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <h1 className="text-3xl font-bold mb-8 gradient-text">Verify Scientific Claims</h1>

      <form onSubmit={handleSubmit} className="card mb-8">
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Claim Text</label>
          <textarea
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
            placeholder="Enter a scientific claim to verify..."
            className="w-full bg-slate-900 border border-slate-600 rounded-lg p-3 text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
            rows="4"
          />
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Domain</label>
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="w-full bg-slate-900 border border-slate-600 rounded-lg p-3 text-white focus:outline-none focus:border-purple-500"
          >
            <option value="medicine">Medicine</option>
            <option value="biology">Biology</option>
            <option value="physics">Physics</option>
            <option value="chemistry">Chemistry</option>
            <option value="general">General Science</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="btn btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {loading ? <FaSpinner className="animate-spin" /> : null}
          {loading ? 'Verifying...' : 'Verify Claim'}
        </button>
      </form>

      {error && (
        <div className="card bg-red-500/20 border-red-500/50 text-red-200 mb-8">
          {error}
        </div>
      )}

      {result && (
        <div className="space-y-6">
          <div className={`card border-2 ${getVerdictColor(result.verdict)}`}>
            <div className="flex justify-between items-start mb-4">
              <div>
                <p className="text-sm opacity-75">Verdict</p>
                <h2 className="text-2xl font-bold">{result.verdict.replace(/_/g, ' ')}</h2>
              </div>
              <div className="text-right">
                <p className="text-sm opacity-75">Confidence</p>
                <p className="text-2xl font-bold">{(result.confidence * 100).toFixed(1)}%</p>
              </div>
            </div>
            <p className="text-gray-200">{result.explanation}</p>
          </div>

          {result.triples && result.triples.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-bold mb-4">Extracted Causal Triples</h3>
              <div className="space-y-2">
                {result.triples.map((triple, idx) => (
                  <div key={idx} className="bg-slate-900/50 p-3 rounded border border-slate-700">
                    <p>
                      <span className="text-cyan-400">{triple.subject}</span>
                      <span className="mx-2">→</span>
                      <span className="text-purple-400">{triple.relation}</span>
                      <span className="mx-2">→</span>
                      <span className="text-green-400">{triple.object}</span>
                    </p>
                    <div className="flex gap-4 mt-2 text-sm text-gray-400">
                      <span>Confidence: {(triple.confidence * 100).toFixed(1)}%</span>
                      <span className={`px-2 py-1 rounded ${triple.status === 'INVALID' ? 'bg-red-500/30' : 'bg-green-500/30'}`}>
                        {triple.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.evidence && result.evidence.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-bold mb-4">Evidence</h3>
              <div className="space-y-3">
                {result.evidence.map((ev, idx) => (
                  <div key={idx} className="bg-slate-900/50 p-3 rounded border border-slate-700">
                    <p className="font-medium text-purple-300">{ev.title}</p>
                    <p className="text-sm text-gray-400 my-2">{ev.snippet}</p>
                    <a href={ev.url} target="_blank" rel="noopener noreferrer" className="text-cyan-400 hover:text-cyan-300 text-sm">
                      {ev.pmid}
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.missing_mechanism && result.missing_mechanism.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-bold mb-4">Missing Mechanisms</h3>
              <ul className="space-y-2">
                {result.missing_mechanism.map((mechanism, idx) => (
                  <li key={idx} className="text-gray-300 flex gap-2">
                    <span className="text-yellow-500">⚠</span>
                    {mechanism}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

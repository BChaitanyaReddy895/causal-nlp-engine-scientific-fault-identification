import React from 'react';
import { Link } from 'react-router-dom';
import { FaArrowRight, FaDatabase, FaNetworkWired, FaBrain } from 'react-icons/fa';

export default function Home() {
  return (
    <div className="max-w-6xl mx-auto px-6 py-20">
      <section className="text-center mb-20">
        <h1 className="text-5xl font-bold mb-4 gradient-text">
          Detect Causal Fallacies in Scientific Claims
        </h1>
        <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
          Beyond fact-checking: AI-powered detection of causal inconsistencies using neural causal structure learning.
        </p>
        <Link to="/verify" className="btn btn-primary inline-flex items-center gap-2">
          Start Verifying <FaArrowRight />
        </Link>
      </section>

      <section className="grid md:grid-cols-3 gap-6 mb-20">
        <div className="card">
          <FaBrain className="text-purple-400 text-3xl mb-4" />
          <h3 className="text-lg font-bold mb-2">Neural Causal Learning</h3>
          <p className="text-gray-400">
            Differentiable DAG learning with Graph Attention Networks for mechanistic validation.
          </p>
        </div>
        <div className="card">
          <FaDatabase className="text-cyan-400 text-3xl mb-4" />
          <h3 className="text-lg font-bold mb-2">Knowledge Integration</h3>
          <p className="text-gray-400">
            UMLS, DisGeNET, and CTD integration for evidence-based causal verification.
          </p>
        </div>
        <div className="card">
          <FaNetworkWired className="text-green-400 text-3xl mb-4" />
          <h3 className="text-lg font-bold mb-2">Counterfactual Reasoning</h3>
          <p className="text-gray-400">
            Identify missing mechanistic pathways and explain causal implausibility.
          </p>
        </div>
      </section>

      <section className="card">
        <h2 className="text-2xl font-bold mb-4">How It Works</h2>
        <div className="space-y-4 text-gray-300">
          <p>✓ <strong>Extract Causality:</strong> Identify causal triples from claims using transformer models</p>
          <p>✓ <strong>Build Graph:</strong> Construct causal graph and learn its structure</p>
          <p>✓ <strong>Verify Evidence:</strong> Query knowledge graphs for supporting evidence</p>
          <p>✓ <strong>Detect Fallacies:</strong> Identify mechanistic gaps and causal inconsistencies</p>
          <p>✓ <strong>Explain:</strong> Provide natural-language reasoning for verdicts</p>
        </div>
      </section>
    </div>
  );
}

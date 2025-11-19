import React from 'react';

export default function About() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <h1 className="text-3xl font-bold mb-8 gradient-text">About Causal-NLP Engine</h1>

      <div className="space-y-6">
        <div className="card">
          <h2 className="text-2xl font-bold mb-3">What is This?</h2>
          <p className="text-gray-300">
            The Causal-NLP Engine is the world's first system dedicated to detecting not just false information, 
            but the causal fallacies embedded within scientific claims. While traditional fact-checking answers 
            "Is this true?", our system answers "Is the causal mechanism scientifically valid?"
          </p>
        </div>

        <div className="card">
          <h2 className="text-2xl font-bold mb-3">Key Innovation</h2>
          <p className="text-gray-300 mb-3">
            We use a unique three-step approach:
          </p>
          <ul className="space-y-2 text-gray-300">
            <li>🔹 <strong>Extract Causality:</strong> Identify causal relationships in claims</li>
            <li>🔹 <strong>Learn Structure:</strong> Build and analyze causal graphs using neural networks</li>
            <li>🔹 <strong>Verify Evidence:</strong> Check mechanistic validity against biomedical knowledge bases</li>
          </ul>
        </div>

        <div className="card">
          <h2 className="text-2xl font-bold mb-3">Technology</h2>
          <p className="text-gray-300 mb-3">
            Built with cutting-edge AI and knowledge management:
          </p>
          <ul className="grid grid-cols-2 gap-3 text-gray-300">
            <li>🔬 Transformer Models (T5, DeBERTa)</li>
            <li>📊 Graph Neural Networks (GAT)</li>
            <li>🧠 Causal Discovery Algorithms</li>
            <li>📚 UMLS, DisGeNET, CTD Knowledge Graphs</li>
          </ul>
        </div>

        <div className="card">
          <h2 className="text-2xl font-bold mb-3">Use Cases</h2>
          <ul className="space-y-2 text-gray-300">
            <li>✅ Detect medical misinformation with mechanistic validation</li>
            <li>✅ Identify unsubstantiated health claims</li>
            <li>✅ Validate scientific arguments and hypotheses</li>
            <li>✅ Support fact-checking with causal analysis</li>
            <li>✅ Assist researchers in literature review</li>
          </ul>
        </div>

        <div className="card">
          <h2 className="text-2xl font-bold mb-3">Research Foundation</h2>
          <p className="text-gray-300 mb-3">
            This system is based on recent advances in:
          </p>
          <ul className="list-disc list-inside space-y-1 text-gray-300">
            <li>Neural Causal Structure Learning</li>
            <li>Biomedical NLP and entity linking</li>
            <li>Knowledge graph reasoning</li>
            <li>Scientific claim verification</li>
            <li>Counterfactual reasoning in NLP</li>
          </ul>
        </div>

        <div className="card">
          <h2 className="text-2xl font-bold mb-3">Limitations & Future Work</h2>
          <p className="text-gray-300 mb-3">
            <strong>Current Limitations:</strong> System focuses on biomedical domain, requires 
            well-documented entities in knowledge graphs, and works best with English-language claims.
          </p>
          <p className="text-gray-300">
            <strong>Future Enhancements:</strong> Cross-domain support, temporal reasoning for evolving 
            research, automatic mechanism explanation generation, and interactive user refinement.
          </p>
        </div>

        <div className="card">
          <h2 className="text-2xl font-bold mb-3">Citation</h2>
          <pre className="bg-slate-900 p-4 rounded text-sm text-purple-300 overflow-auto">
{`@software{causalnlp2025,
  title={Causal-NLP Engine for Fake Scientific Claims Detection},
  author={Causal-NLP Initiative},
  year={2025},
  url={https://github.com/causal-nlp/claim-verifier}
}`}
          </pre>
        </div>

        <div className="card">
          <h2 className="text-2xl font-bold mb-3">Open Source</h2>
          <p className="text-gray-300 mb-3">
            This project is open source and available on GitHub under the MIT license.
          </p>
          <a href="#" className="text-purple-400 hover:text-purple-300">
            → View on GitHub
          </a>
        </div>
      </div>
    </div>
  );
}

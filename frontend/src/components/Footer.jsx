import React from 'react';

export default function Footer() {
  return (
    <footer className="bg-slate-900/50 border-t border-slate-700/50 mt-12">
      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="grid grid-cols-3 gap-8 mb-8">
          <div>
            <h3 className="font-bold mb-3">About</h3>
            <p className="text-gray-400 text-sm">
              Detecting causal fallacies in scientific claims using neural networks.
            </p>
          </div>
          <div>
            <h3 className="font-bold mb-3">Resources</h3>
            <ul className="text-gray-400 text-sm space-y-1">
              <li><a href="#" className="hover:text-purple-400">Documentation</a></li>
              <li><a href="#" className="hover:text-purple-400">API Reference</a></li>
              <li><a href="#" className="hover:text-purple-400">Research Paper</a></li>
            </ul>
          </div>
          <div>
            <h3 className="font-bold mb-3">Legal</h3>
            <ul className="text-gray-400 text-sm space-y-1">
              <li><a href="#" className="hover:text-purple-400">Privacy</a></li>
              <li><a href="#" className="hover:text-purple-400">Terms</a></li>
              <li><a href="#" className="hover:text-purple-400">License</a></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-slate-700/50 pt-6 text-center text-gray-500 text-sm">
          <p>&copy; 2025 Causal-NLP Initiative. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}

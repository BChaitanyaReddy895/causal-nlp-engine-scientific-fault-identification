import React from 'react';
import { Link } from 'react-router-dom';
import { FaGithub, FaTwitter, FaLinkedin } from 'react-icons/fa';

export default function Header() {
  return (
    <header className="bg-slate-800/50 backdrop-blur-md border-b border-slate-700/50 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
        <Link to="/" className="flex items-center gap-2">
          <div className="text-2xl font-bold gradient-text">🧠 Causal-NLP</div>
        </Link>
        <nav className="flex items-center gap-6">
          <Link to="/" className="hover:text-purple-400 transition">Home</Link>
          <Link to="/verify" className="hover:text-purple-400 transition">Verify</Link>
          <Link to="/about" className="hover:text-purple-400 transition">About</Link>
          <div className="flex gap-3">
            <a href="#" className="text-gray-400 hover:text-purple-400"><FaGithub size={20} /></a>
            <a href="#" className="text-gray-400 hover:text-purple-400"><FaTwitter size={20} /></a>
            <a href="#" className="text-gray-400 hover:text-purple-400"><FaLinkedin size={20} /></a>
          </div>
        </nav>
      </div>
    </header>
  );
}

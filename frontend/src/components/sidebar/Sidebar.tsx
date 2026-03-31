import { Link, useLocation } from 'react-router-dom';
import { MessageSquare, Network, Settings, Shield, User } from 'lucide-react';
import ModeSelector from './ModeSelector';

export function Sidebar() {
  const location = useLocation();
  const isActive = (path: string) => location.pathname === path;
  const linkClass = (path: string) => "flex items-center gap-3 px-3 py-2 rounded-md transition-colors " + (isActive(path) ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white hover:bg-slate-800");

  return (
    <div className="w-64 h-full bg-slate-950 text-slate-300 flex flex-col">
      <div className="p-4 flex items-center gap-2 border-b border-slate-800">
        <Network className="w-6 h-6 text-blue-500" />
        <span className="text-xl font-bold text-white">NeuroGraph</span>
      </div>
      <div className="p-4"><ModeSelector /></div>
      <nav className="flex-1 px-4 py-2 space-y-1">
        <Link to="/chat" className={linkClass('/chat')}><MessageSquare className="w-5 h-5" /> Chat</Link>
        <Link to="/graph" className={linkClass('/graph')}><Network className="w-5 h-5" /> Knowledge Graph</Link>
      </nav>
      <div className="px-4 py-4 space-y-1 border-t border-slate-800">
        <Link to="/settings" className={linkClass('/settings')}><Settings className="w-5 h-5" /> Settings</Link>
        <Link to="/admin" className={linkClass('/admin')}><Shield className="w-5 h-5" /> Administration</Link>
        <div className="flex items-center gap-3 px-3 py-2 mt-4">
          <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center"><User className="w-5 h-5" /></div>
          <div className="text-sm"><p className="text-white font-medium">User</p><p className="text-xs text-slate-500">user@example.com</p></div>
        </div>
      </div>
    </div>
  );
}


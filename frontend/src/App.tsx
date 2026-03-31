import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';
import { TooltipProvider } from '@/components/ui/tooltip';
import { AppSidebar } from '@/components/sidebar/AppSidebar';
import Chat from '@/pages/Chat';
import Graph from '@/pages/Graph';
import Login from '@/pages/Login';
import Settings from '@/pages/Settings';
import Admin from '@/pages/Admin';
import { Sparkles } from 'lucide-react';
import { useMemo } from 'react';
import { cn } from '@/lib/utils';

function Layout() {
  const location = useLocation();
  const isChatRoute = location.pathname.startsWith('/chat');
  const pageTitle = useMemo(() => {
    if (location.pathname.startsWith('/graph')) return 'Knowledge Graph';
    if (location.pathname.startsWith('/settings')) return 'System Settings';
    if (location.pathname.startsWith('/admin')) return 'Admin Center';
    return 'Intelligence Chat';
  }, [location.pathname]);

  return (
    <SidebarProvider defaultOpen>
      <div className="app-shell flex h-dvh min-h-dvh w-full text-white selection:bg-primary selection:text-primary-foreground">
        <AppSidebar />
        <main className="relative flex h-full min-w-0 flex-1 flex-col overflow-hidden border-l border-white/10 bg-[#090512]">
          <div className="pointer-events-none absolute inset-0 opacity-55">
            <div className="absolute -top-24 right-10 h-52 w-52 rounded-full bg-purple-400/25 blur-[76px]" />
            <div className="absolute bottom-0 left-1/4 h-44 w-44 rounded-full bg-fuchsia-500/18 blur-[72px]" />
          </div>

          {isChatRoute ? (
            <div className="pointer-events-none absolute left-3 top-3 z-20 flex items-center gap-2 md:left-4 md:top-4">
              <SidebarTrigger className="pointer-events-auto size-9 rounded-full border border-white/15 bg-black/25 text-white/75 hover:bg-white/10 hover:text-white" />
              <div className="rounded-full border border-white/10 bg-black/25 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em] text-white/65 backdrop-blur-sm">
                Intelligence Chat
              </div>
            </div>
          ) : (
            <header className="relative z-20 flex shrink-0 items-center justify-between border-b border-white/10 px-4 py-3 md:px-6 md:py-4">
              <div className="flex min-w-0 items-center gap-3">
                <SidebarTrigger className="size-9 rounded-full border border-white/15 bg-white/5 text-white/70 hover:bg-white/10 hover:text-white" />
                <div className="min-w-0">
                  <p className="text-xs uppercase tracking-[0.25em] text-white/45">NeuroGraph Workspace</p>
                  <h1 className="truncate text-lg font-semibold tracking-tight text-white md:text-xl">{pageTitle}</h1>
                </div>
              </div>
              <div className="hidden items-center gap-2 rounded-full border border-purple-300/20 bg-purple-300/8 px-3 py-1 text-xs text-purple-100 md:flex">
                <Sparkles className="size-3.5 text-purple-200" />
                Real-time AI + Graph Intelligence
              </div>
            </header>
          )}

          <div className={cn('relative z-10 flex-1 min-h-0', isChatRoute ? 'flex h-full min-h-0 overflow-hidden p-0' : 'overflow-y-auto p-2 md:p-4')}>
            <Routes>
              <Route path="/" element={<Navigate to="/chat" replace />} />
              <Route path="/chat" element={<div className="flex h-full min-h-0 w-full"><Chat /></div>} />
              <Route path="/graph" element={<Graph />} />
              <Route path="/settings" element={<Settings />} />
              <Route path="/admin" element={<Admin />} />
            </Routes>
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}

function App() {
  return (
    <Router>
      <TooltipProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={<Layout />} />
        </Routes>
      </TooltipProvider>
    </Router>
  );
}

export default App;


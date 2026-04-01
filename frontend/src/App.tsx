import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';
import { TooltipProvider } from '@/components/ui/tooltip';
import { AppSidebar } from '@/components/sidebar/AppSidebar';
import Landing from '@/pages/Landing';
import Chat from '@/pages/Chat';
import Graph from '@/pages/Graph';
import Login from '@/pages/Login';
import Signup from '@/pages/Signup';
import Admin from '@/pages/Admin';
import Memory from '@/pages/Memory';
import Profile from '@/pages/Profile';
import Integrations from '@/pages/Integrations';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { ThemeProvider, useTheme } from '@/contexts/ThemeContext';
import { Sparkles } from 'lucide-react';
import { useMemo } from 'react';
import { cn } from '@/lib/utils';

// Protected route wrapper
function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-dvh items-center justify-center bg-[#090512]">
        <div className="animate-pulse text-white/60">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

function Layout() {
  const location = useLocation();
  useAuth(); // Ensure user is authenticated
  const { sidebarCollapsed, setSidebarCollapsed, compactMode, showConfidence, showReasoning } = useTheme();
  const isChatRoute = location.pathname.startsWith('/chat') || location.pathname === '/';
  const isFullscreenRoute = isChatRoute || location.pathname.startsWith('/graph') || location.pathname.startsWith('/memory');
  const pageTitle = useMemo(() => {
    if (location.pathname.startsWith('/graph')) return 'Knowledge Graph';
    if (location.pathname.startsWith('/memory')) return 'Memory Store';
    if (location.pathname.startsWith('/settings')) return 'System Settings';
    if (location.pathname.startsWith('/admin')) return 'Admin Center';
    if (location.pathname.startsWith('/profile')) return 'Profile & Settings';
    if (location.pathname.startsWith('/integrations')) return 'Integrations';
    return 'Intelligence Chat';
  }, [location.pathname]);

  return (
    <SidebarProvider open={!sidebarCollapsed} onOpenChange={(open) => setSidebarCollapsed(!open)}>
      <div className="app-shell flex h-dvh min-h-dvh w-full text-white selection:bg-primary selection:text-primary-foreground">
        <AppSidebar />
        <main className="relative flex h-full min-w-0 flex-1 flex-col overflow-hidden border-l border-white/10 bg-[#090512]">
          <div className="pointer-events-none absolute inset-0 opacity-55">
            <div className="absolute -top-24 right-10 h-52 w-52 rounded-full bg-purple-400/25 blur-[76px]" />
            <div className="absolute bottom-0 left-1/4 h-44 w-44 rounded-full bg-fuchsia-500/18 blur-[72px]" />
          </div>

          <header className={cn(
            'relative z-20 flex shrink-0 items-center justify-between border-b border-white/10 bg-[#090512] px-4 md:px-6',
            compactMode ? 'py-2 md:py-2.5' : 'py-3 md:py-4',
          )}>
            <div className="flex min-w-0 items-center gap-3">
              <SidebarTrigger className="size-9 rounded-full border border-white/15 bg-white/5 text-white/70 hover:bg-white/10 hover:text-white" />
              <div className="min-w-0">
                <p className="text-xs uppercase tracking-[0.25em] text-white/45">NeuroGraph Workspace</p>
                <h1 className="truncate text-lg font-semibold tracking-tight text-white md:text-xl">{pageTitle}</h1>
              </div>
            </div>
            <div className="hidden items-center gap-3 rounded-full border border-purple-300/20 bg-purple-300/8 px-3 py-1 text-xs text-purple-100 md:flex">
              <Sparkles className="size-3.5 text-purple-200" />
              Real-time AI + Graph Intelligence
              <span className="text-purple-100/60">•</span>
              <span className="text-purple-100/80">{showReasoning ? 'Reasoning On' : 'Reasoning Off'}</span>
              <span className="text-purple-100/60">•</span>
              <span className="text-purple-100/80">{showConfidence ? 'Confidence On' : 'Confidence Off'}</span>
            </div>
          </header>

          <div
            className={cn(
              'relative z-10 flex-1 min-h-0 flex flex-col w-full',
              isFullscreenRoute ? 'overflow-hidden p-0' : compactMode ? 'overflow-y-auto p-1.5 md:p-2.5' : 'overflow-y-auto p-2 md:p-4',
            )}
          >
            <Routes>
              <Route path="/" element={<Navigate to="/chat" replace />} />      
              <Route path="/chat" element={<Chat />} />
              <Route path="/chat/:conversationId" element={<Chat />} />
              <Route path="/graph" element={<Graph />} />
              <Route path="/memory" element={<Memory />} />
              <Route path="/settings" element={<Navigate to="/profile/settings" replace />} />
              <Route path="/profile" element={<Profile />} />
              <Route path="/profile/*" element={<Profile />} />
              <Route path="/integrations" element={<Integrations />} />
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
      <AuthProvider>
        <ThemeProvider>
          <TooltipProvider>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/*" element={
                <RequireAuth>
                  <Layout />
                </RequireAuth>
              } />
            </Routes>
          </TooltipProvider>
        </ThemeProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;


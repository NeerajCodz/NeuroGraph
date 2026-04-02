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
import NotFound from '@/pages/NotFound';
import { AuthProvider, useAuth } from '@/contexts/AuthContext';
import { ThemeProvider, useTheme } from '@/contexts/ThemeContext';
import { useMemo } from 'react';
import { cn } from '@/lib/utils';
import { useRouteSeo } from '@/lib/seo';

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
    const knownProtectedPrefixes = ['/chat', '/graph', '/memory', '/settings', '/profile', '/integrations', '/admin'];
    const isKnownProtectedPath = knownProtectedPrefixes.some((prefix) => location.pathname.startsWith(prefix));
    if (!isKnownProtectedPath) {
      return <Navigate to="/404" replace />;
    }
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

function Layout() {
  const location = useLocation();
  useAuth(); // Ensure user is authenticated
  const { sidebarCollapsed, setSidebarCollapsed, compactMode } = useTheme();
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
    <SidebarProvider
      open={!sidebarCollapsed}
      onOpenChange={(open) => setSidebarCollapsed(!open)}
      className="app-shell text-white selection:bg-primary selection:text-primary-foreground"
    >
      <AppSidebar />
      <main className="relative flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden border-l border-white/10 bg-[#090512]">
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
        </header>

        <div
          className={cn(
            'relative z-10 flex flex-1 min-h-0 w-full flex-col',
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
            <Route path="*" element={<Navigate to="/404" replace />} />
          </Routes>
        </div>
      </main>
    </SidebarProvider>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <ThemeProvider>
          <TooltipProvider>
            <AppRoutes />
          </TooltipProvider>
        </ThemeProvider>
      </AuthProvider>
    </Router>
  );
}

function AppRoutes() {
  const location = useLocation();
  useRouteSeo(location.pathname);

  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/404" element={<NotFound />} />
      <Route
        path="/*"
        element={(
          <RequireAuth>
            <Layout />
          </RequireAuth>
        )}
      />
    </Routes>
  );
}

export default App;


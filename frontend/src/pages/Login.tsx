import React, { useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Network, ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import LiquidEther from '@/components/landing/LiquidEther';
import { useAuth } from '@/contexts/AuthContext';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Redirect if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as { from?: Location })?.from?.pathname || '/chat';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location.state]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);
    
    try {
      await login(email, password);
      const from = (location.state as { from?: Location })?.from?.pathname || '/chat';
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  // Memoize the background to prevent it from re-rendering on every keystroke
  const background = React.useMemo(() => (
    <div className="absolute inset-0 z-0 opacity-80 pointer-events-none">
      <LiquidEther
          colors={['#5227FF', '#FF9FFC', '#B19EEF']}
          mouseForce={20}
          cursorSize={100}
          isViscous
          viscous={30}
          iterationsViscous={32}
          iterationsPoisson={32}
          resolution={0.5}
          isBounce={false}
          autoDemo
          autoSpeed={0.5}
          autoIntensity={2.2}
          takeoverDuration={0.25}
          autoResumeDelay={3000}
          autoRampDuration={0.6}
          color0="#5227FF"
          color1="#FF9FFC"
          color2="#B19EEF"
      />
      <div className="absolute inset-0 bg-[#050110]/20 mix-blend-multiply" />
    </div>
  ), []);

  return (
    <div className="relative flex h-screen w-full bg-[#050110] items-center justify-center overflow-hidden text-white font-sans">
      
      {/* 1. Full Screen Liquid Ether Background */}
      {background}

      {/* Back Button */}
      <Link 
        to="/" 
        className="absolute top-6 left-6 z-50 flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm font-medium hover:bg-white/10 transition-colors backdrop-blur-md"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Home
      </Link>

      {/* 2. Simplified Black Glass Auth Popup */}
      <div className="relative z-10 w-full max-w-[400px]">
        <Card className="border border-white/10 bg-black/60 shadow-[0_0_60px_rgba(82,39,255,0.2)] backdrop-blur-2xl rounded-3xl p-6 md:p-8">
          <CardHeader className="space-y-4 px-0 pt-0 pb-6 flex flex-col items-center text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#5227FF] to-[#8638FF] border border-white/20 shadow-[0_4px_20px_rgba(82,39,255,0.4)]">
              <Network className="h-7 w-7 text-white" />
            </div>
            <div className="space-y-1">
              <CardTitle className="text-2xl font-bold tracking-tight text-white drop-shadow-md">
                Welcome Back
              </CardTitle>
              <CardDescription className="text-purple-200/60 font-medium">
                NeuroGraph Core
              </CardDescription>
            </div>
          </CardHeader>

          <CardContent className="px-0">
            <form onSubmit={handleLogin} className="space-y-4">
              {error && (
                <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-200 text-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </div>
              )}
              <Input 
                type="email" 
                placeholder="name@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
                className="h-12 border-white/10 bg-black/50 text-white placeholder:text-white/40 focus-visible:border-purple-500/50 focus-visible:ring-purple-500/30 rounded-xl transition-colors" 
              />
              <Input 
                type="password" 
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
                className="h-12 border-white/10 bg-black/50 text-white placeholder:text-white/40 focus-visible:border-purple-500/50 focus-visible:ring-purple-500/30 rounded-xl transition-colors" 
              />
              <Button 
                type="submit"
                disabled={isLoading}
                className="h-12 w-full text-base font-semibold text-white bg-gradient-to-r from-[#5227FF] to-[#8638FF] hover:from-[#663fff] hover:to-[#9a54ff] transition-all rounded-xl shadow-[0_0_20px_rgba(82,39,255,0.3)] border border-purple-400/20 mt-4 disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  'Sign In'
                )}
              </Button>
              
              <div className="mt-8 text-center text-sm text-white/50 font-medium">
                Don't have an account?{' '}
                <Link to="/signup" className="text-white hover:text-purple-300 transition-colors ml-1">
                  Create one
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>

    </div>
  );
}

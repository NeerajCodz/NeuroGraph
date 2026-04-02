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
import { ArrowLeft, Loader2, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import LiquidEther from '@/components/landing/LiquidEther';
import { useAuth } from '@/contexts/AuthContext';
import BorderGlow from '@/components/reactbits/BorderGlow';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
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
      <BorderGlow 
        className="relative z-10 w-full max-w-[400px] border-none"
        glowColor="300 80 50" 
        borderRadius={32}
        glowRadius={40}
        glowIntensity={1.2}
        colors={['#c084fc', '#FF9FFC', '#5227FF']}
        fillOpacity={0}
        edgeSensitivity={30}
      >
        <Card 
          className="w-full relative overflow-hidden bg-black/60 backdrop-blur-2xl rounded-[32px] text-white transition-all duration-300"
          style={{
            border: 'none',
            borderTop: '0.5px solid rgba(255,255,255,0.1)',
            borderLeft: '0.5px solid rgba(255,255,255,0.05)',
            borderRight: '0.5px solid rgba(0,0,0,0.4)',
            borderBottom: '1px solid rgba(0,0,0,0.8)',
            boxShadow: 'inset 0 1px 2px rgba(255,255,255,0.1), inset 0 -4px 10px rgba(0,0,0,0.8), 0 15px 30px rgba(0,0,0,0.6)'
          }}
        >
          <CardHeader className="space-y-4 px-6 pt-10 pb-6 flex flex-col items-center text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-600 via-purple-500 to-fuchsia-600 shadow-[0_0_30px_rgba(168,85,247,0.4)] border border-white/20 p-3">
              <img src="/logo.svg" alt="NeuroGraph" className="w-full h-full brightness-0 invert drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]" />
            </div>
            <div className="space-y-1">
              <CardTitle className="text-3xl font-bold tracking-tight text-white drop-shadow-md">
                Welcome Back
              </CardTitle>
              <CardDescription className="text-purple-200/60 font-medium">
                NeuroGraph Core
              </CardDescription>
            </div>
          </CardHeader>

          <CardContent className="px-8 pb-10">
            <form onSubmit={handleLogin} className="space-y-5">
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
                className="h-12 bg-white/5 border-white/10 text-white placeholder:text-white/30 rounded-xl focus-visible:ring-purple-500 focus-visible:border-purple-500 transition-all font-medium px-4" 
              />
              <div className="relative">
                <Input
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                  className="h-12 bg-white/5 border-white/10 text-white placeholder:text-white/30 rounded-xl focus-visible:ring-fuchsia-500 focus-visible:border-fuchsia-500 transition-all font-medium px-4 pr-11 tracking-widest"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  disabled={isLoading}
                  className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-white/45 transition hover:text-white/80 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              
              <div className="mt-6 flex flex-col gap-4">
                <BorderGlow borderRadius={12} glowRadius={15} glowIntensity={1.5} edgeSensitivity={10} className="w-full">
                  <Button 
                    type="submit"
                    disabled={isLoading}
                    className="h-12 w-full text-[15px] font-bold text-white bg-gradient-to-r from-purple-600 to-fuchsia-500 hover:from-purple-500 hover:to-fuchsia-400 transition-all rounded-xl border-none disabled:opacity-50 active:scale-[0.98]"
                    style={{
                      boxShadow: 'inset 0 2px 3px rgba(255,255,255,0.4), inset 0 -3px 6px rgba(0,0,0,0.6), 0 0 20px rgba(212,166,255,0.4)',
                      borderTop: '1px solid rgba(255,255,255,0.3)',
                      borderBottom: '2px solid rgba(0,0,0,0.8)',
                      textShadow: '0 1px 2px rgba(0,0,0,0.8)'
                    }}
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
                </BorderGlow>
              </div>
              
              <div className="mt-8 text-center text-sm text-purple-200/50 font-medium">
                Don't have an account?{' '}
                <Link to="/signup" className="text-purple-400 hover:text-purple-300 font-bold ml-1 relative after:absolute after:bottom-0 after:left-0 after:w-full after:h-px after:bg-purple-400/50 hover:after:bg-purple-300/100 after:transition-colors">
                  Create one
                </Link>
              </div>
            </form>
          </CardContent>
        </Card>
      </BorderGlow>

    </div>
  );
}

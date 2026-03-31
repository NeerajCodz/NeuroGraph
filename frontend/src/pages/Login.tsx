import React from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Network, LockKeyhole } from 'lucide-react';
import { Particles } from '@/components/animations/Particles';
import { BlurText } from '@/components/reactbits/BlurText';
import { SpotlightCard } from '@/components/reactbits/SpotlightCard';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const navigate = useNavigate();
  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    navigate('/chat');
  };

  return (
    <div className="fixed inset-0 flex h-screen w-screen items-center justify-center overflow-hidden bg-[#05020f]">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-[-6%] top-[-8%] h-72 w-72 rounded-full bg-purple-500/35 blur-[90px]" />
        <div className="absolute right-[-5%] top-[42%] h-80 w-80 rounded-full bg-fuchsia-500/20 blur-[110px]" />
        <div className="absolute bottom-[-16%] left-[26%] h-80 w-80 rounded-full bg-indigo-500/25 blur-[110px]" />
      </div>

      <Particles color="rgba(197, 151, 255, 0.24)" count={110} />

      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        className="relative z-10 w-full max-w-md p-4"
      >
        <SpotlightCard className="glass-panel purple-stroke rounded-3xl border-white/15" spotlightColor="rgba(188, 137, 255, 0.3)">
          <Card className="border-none bg-transparent text-slate-100 shadow-none">
            <CardHeader className="items-center space-y-4 pt-8">
              <div className="gradient-primary flex h-16 w-16 items-center justify-center rounded-2xl border border-white/20 shadow-[0_16px_26px_-14px_rgba(164,109,255,1)]">
                <Network className="h-8 w-8 text-primary-foreground" />
              </div>

              <div className="text-center space-y-2">
                <CardTitle className="text-3xl font-bold tracking-tight text-white">
                  <BlurText text="NeuroGraph" delay={50} direction="bottom" animateBy="letters" />
                </CardTitle>
                <CardDescription className="text-white/65">
                  Enterprise Knowledge Context System
                </CardDescription>
              </div>
            </CardHeader>

            <CardContent>
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-2">
                  <Input type="email" placeholder="name@example.com" className="h-12 border-white/12 bg-black/25 text-white placeholder:text-white/35 focus-visible:border-purple-300/40 focus-visible:ring-purple-400/35" />
                </div>
                <div className="space-y-2">
                  <Input type="password" placeholder="••••••••" className="h-12 border-white/12 bg-black/25 text-white placeholder:text-white/35 focus-visible:border-purple-300/40 focus-visible:ring-purple-400/35" />
                </div>
                <Button type="submit" className="gradient-primary h-11 w-full text-md font-semibold text-primary-foreground transition-all hover:brightness-110">
                  Sign In
                </Button>
              </form>
            </CardContent>

            <CardFooter className="flex-col justify-center gap-2 pb-7 pt-2">
              <div className="flex items-center gap-2 text-xs text-white/50">
                <LockKeyhole className="h-3.5 w-3.5" />
                By signing in, you agree to our Terms of Service
              </div>
            </CardFooter>
          </Card>
        </SpotlightCard>
      </motion.div>
    </div>
  );
}


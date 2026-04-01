import { useState } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { motion } from 'framer-motion';
import BorderGlow from '@/components/reactbits/BorderGlow';

export default function LoginCard() {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <BorderGlow 
      className="w-full max-w-[400px]"
      glowColor="300 80 50" 
      borderRadius={32}
      glowRadius={40}
      glowIntensity={1.2}
      colors={['#c084fc', '#FF9FFC', '#5227FF']}
      fillOpacity={0}
      edgeSensitivity={30}
    >
      <Card 
        className="w-full relative overflow-hidden bg-black/50 backdrop-blur-2xl rounded-[32px] text-white transition-all duration-300"
        style={{
          border: 'none',
          borderTop: '0.5px solid rgba(255,255,255,0.1)',
          borderLeft: '0.5px solid rgba(255,255,255,0.05)',
          borderRight: '0.5px solid rgba(0,0,0,0.4)',
          borderBottom: '1px solid rgba(0,0,0,0.8)',
          boxShadow: 'inset 0 1px 2px rgba(255,255,255,0.1), inset 0 -4px 10px rgba(0,0,0,0.8), 0 15px 30px rgba(0,0,0,0.6)'
        }}
      >
        {/* Glow / ProfileCard aesthetic background blobs */}
        <div className="absolute top-[-100px] -left-10 w-48 h-48 bg-purple-600/30 rounded-full blur-[80px] pointer-events-none" />
        <div className="absolute bottom-[-100px] -right-10 w-48 h-48 bg-fuchsia-500/20 rounded-full blur-[80px] pointer-events-none" />

        <CardHeader className="pt-10 pb-6 relative z-10 text-center">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="flex flex-col items-center gap-2"
          >
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-[#5227FF] to-[#FF9FFC] flex items-center justify-center p-[2px] shadow-[0_0_20px_rgba(82,39,255,0.4)] mb-4">
              <div className="w-full h-full bg-black/80 rounded-[14px] flex items-center justify-center">
                <span className="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-purple-300 to-fuchsia-300">N</span>
              </div>
            </div>
            <CardTitle className="text-3xl font-bold tracking-tight text-white font-sans">
              Welcome back
            </CardTitle>
            <p className="text-sm font-medium text-purple-200/70">
              {isLogin ? "Sign in to access your agentic brain" : "Create an account to start"}
            </p>
          </motion.div>
        </CardHeader>
        <CardContent className="space-y-5 px-8 relative z-10 pointer-events-auto">
          {!isLogin && (
            <div className="space-y-2">
              <Label htmlFor="name" className="text-purple-200 text-xs font-semibold uppercase tracking-wider ml-1">Full Name</Label>
              <Input
                id="name"
                placeholder="Ada Lovelace"
                className="h-12 bg-white/5 border-white/10 text-white placeholder:text-white/30 rounded-xl focus-visible:ring-purple-500 focus-visible:border-purple-500 transition-all font-medium px-4"
              />
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="email" className="text-purple-200 text-xs font-semibold uppercase tracking-wider ml-1">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="name@example.com"
              className="h-12 bg-white/5 border-white/10 text-white placeholder:text-white/30 rounded-xl focus-visible:ring-purple-500 focus-visible:border-purple-500 transition-all font-medium px-4"
            />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between ml-1">
              <Label htmlFor="password" className="text-purple-200 text-xs font-semibold uppercase tracking-wider">Password</Label>
              {isLogin && <a href="#" className="text-xs font-medium text-fuchsia-400 hover:text-fuchsia-300 transition-colors blur-0">Forgot?</a>}
            </div>
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              className="h-12 bg-white/5 border-white/10 text-white placeholder:text-white/30 rounded-xl focus-visible:ring-fuchsia-500 focus-visible:border-fuchsia-500 transition-all font-medium px-4 tracking-widest"
            />
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-4 mt-4 pb-10 px-8 relative z-10 pointer-events-auto">
          <BorderGlow borderRadius={12} glowRadius={15} glowIntensity={1.5} edgeSensitivity={10} className="w-full">
            <Button 
              className="w-full h-12 bg-gradient-to-r from-purple-600 to-fuchsia-500 hover:from-purple-500 hover:to-fuchsia-400 text-white rounded-xl transition-all font-bold text-[15px] border-none active:scale-[0.98]"
              style={{
                boxShadow: 'inset 0 2px 3px rgba(255,255,255,0.4), inset 0 -3px 6px rgba(0,0,0,0.6), 0 0 20px rgba(212,166,255,0.4)',
                borderTop: '1px solid rgba(255,255,255,0.3)',
                borderBottom: '2px solid rgba(0,0,0,0.8)',
                textShadow: '0 1px 2px rgba(0,0,0,0.8)'
              }}
            >
              {isLogin ? "Sign In" : "Create Account"}
            </Button>
          </BorderGlow>
          <div className="text-center text-sm font-medium text-purple-200/50 mt-2">
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button
              onClick={() => setIsLogin(!isLogin)}
              className="text-purple-400 hover:text-purple-300 transition-colors font-bold relative after:absolute after:bottom-0 after:left-0 after:w-full after:h-px after:bg-purple-400/50 hover:after:bg-purple-300/100 after:transition-colors"
            >
              {isLogin ? "Sign up" : "Log in"}
            </button>
          </div>
        </CardFooter>
      </Card>
    </BorderGlow>
  );
}

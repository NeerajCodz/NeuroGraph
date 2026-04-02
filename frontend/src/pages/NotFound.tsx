import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Home, SearchX } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import LiquidEther from '@/components/landing/LiquidEther';
import BorderGlow from '@/components/reactbits/BorderGlow';

export default function NotFound() {
  const background = React.useMemo(
    () => (
      <div className="pointer-events-none absolute inset-0 z-0 opacity-80">
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
    ),
    []
  );

  return (
    <div className="relative flex h-screen w-full items-center justify-center overflow-hidden bg-[#050110] font-sans text-white">
      {background}

      <Link
        to="/"
        className="absolute top-6 left-6 z-50 flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-medium backdrop-blur-md transition-colors hover:bg-white/10"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Home
      </Link>

      <BorderGlow
        className="relative z-10 w-full max-w-[420px] border-none"
        glowColor="300 80 50"
        borderRadius={32}
        glowRadius={40}
        glowIntensity={1.2}
        colors={['#c084fc', '#FF9FFC', '#5227FF']}
        fillOpacity={0}
        edgeSensitivity={30}
      >
        <Card
          className="relative w-full overflow-hidden rounded-[32px] bg-black/60 text-white backdrop-blur-2xl transition-all duration-300"
          style={{
            border: 'none',
            borderTop: '0.5px solid rgba(255,255,255,0.1)',
            borderLeft: '0.5px solid rgba(255,255,255,0.05)',
            borderRight: '0.5px solid rgba(0,0,0,0.4)',
            borderBottom: '1px solid rgba(0,0,0,0.8)',
            boxShadow: 'inset 0 1px 2px rgba(255,255,255,0.1), inset 0 -4px 10px rgba(0,0,0,0.8), 0 15px 30px rgba(0,0,0,0.6)',
          }}
        >
          <CardHeader className="flex flex-col items-center space-y-4 px-6 pt-10 pb-6 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl border border-white/20 bg-gradient-to-br from-purple-600 via-purple-500 to-fuchsia-600 p-3 shadow-[0_0_30px_rgba(168,85,247,0.4)]">
              <SearchX className="h-8 w-8 text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.5)]" />
            </div>
            <div className="space-y-1">
              <CardTitle className="text-3xl font-bold tracking-tight text-white drop-shadow-md">
                Page Not Found
              </CardTitle>
              <CardDescription className="font-medium text-purple-200/60">
                The page you requested does not exist.
              </CardDescription>
            </div>
          </CardHeader>

          <CardContent className="px-8 pb-10">
            <div className="mt-4 flex flex-col gap-3">
              <Link to="/chat" className="w-full">
                <Button
                  className="h-12 w-full rounded-xl border-none bg-gradient-to-r from-purple-600 to-fuchsia-500 text-[15px] font-bold text-white transition-all hover:from-purple-500 hover:to-fuchsia-400"
                  style={{
                    boxShadow: 'inset 0 2px 3px rgba(255,255,255,0.4), inset 0 -3px 6px rgba(0,0,0,0.6), 0 0 20px rgba(212,166,255,0.4)',
                    borderTop: '1px solid rgba(255,255,255,0.3)',
                    borderBottom: '2px solid rgba(0,0,0,0.8)',
                    textShadow: '0 1px 2px rgba(0,0,0,0.8)',
                  }}
                >
                  <Home className="mr-2 h-4 w-4" />
                  Go to Chat
                </Button>
              </Link>
              <Link to="/memory" className="w-full">
                <Button variant="outline" className="h-11 w-full rounded-xl border-white/15 bg-white/5 text-white/85 hover:bg-white/10">
                  Open Memory
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </BorderGlow>
    </div>
  );
}

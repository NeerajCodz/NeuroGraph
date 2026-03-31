import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { BlurText } from '@/components/reactbits/BlurText';
import ScrollFloat from '@/components/text/ScrollFloat';
import ScrollStack, { ScrollStackItem } from '@/components/ScrollStack';
import Silk from '@/components/landing/Silk';
import GridMotion from '@/components/landing/GridMotion';
import Plasma from '@/components/landing/Plasma';
import Hyperspeed from '@/components/landing/Hyperspeed';
import { ArrowRight, Network, Sparkles, DatabaseZap } from 'lucide-react';

// Reusable scroll reveal wrapper
const ScrollReveal = ({ children, className = '', delay = 0 }: any) => (
  <motion.div
    initial={{ opacity: 0, y: 60 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-100px" }}
    transition={{ duration: 0.8, delay, ease: [0.16, 1, 0.3, 1] }}
    className={className}
  >
    {children}
  </motion.div>
);

export default function Landing() {
  return (
    <div className="bg-[#050110] text-white min-h-screen font-sans selection:bg-purple-600/50 selection:text-white overflow-x-hidden">

      {/* 1. HERO SECTION */}
      <section className="relative h-screen w-full flex flex-col items-center justify-center overflow-hidden">
        {/* Hyperspeed background */}
        <div className="absolute inset-0 z-0">
          <Hyperspeed
            effectOptions={{
              distortion: 'turbulentDistortion',
              length: 400,
              roadWidth: 10,
              lanesPerRoad: 4,
              fov: 90,
              fovSpeedUp: 150,
              speedUp: 2,
              carLightsFade: 0.4,
              totalSideLightSticks: 20,
              lightPairsPerRoadWay: 40,
              colors: {
                roadColor: 0x080808,
                islandColor: 0x0a0a0a,
                background: 0x000000,
                shoulderLines: 0x131318,
                brokenLines: 0x131318,
                leftCars: [0x9333ea, 0x7c3aed, 0xa855f7],
                rightCars: [0x06b6d4, 0x0891b2, 0x22d3ee],
                sticks: 0x7c3aed
              }
            }}
          />
        </div>
        
        {/* Gradient overlay for readability */}
        <div className="absolute inset-0 z-[1] bg-gradient-to-b from-[#050110]/60 via-transparent to-[#050110]" />
        <div className="absolute inset-0 z-[1] bg-[radial-gradient(ellipse_at_center,_transparent_0%,_rgba(5,1,16,0.7)_70%)]" />

        <header className="absolute top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-6 md:px-12 pointer-events-auto">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-400 via-purple-300 to-fuchsia-300 shadow-[0_12px_28px_-14px_rgba(212,166,255,0.95)]">
              <Network className="h-5 w-5 text-purple-950 stroke-[2.2]" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white drop-shadow-md">NeuroGraph</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-purple-100">
            <a href="#features" className="hover:text-white transition">Features</a>
            <a href="#orchestrator" className="hover:text-white transition">Orchestrator</a>
            <a href="#data" className="hover:text-white transition">Logic Flow</a>
          </div>
          <Link to="/chat" className="flex items-center gap-2 rounded-full border border-purple-500/30 bg-purple-500/10 px-6 py-2.5 text-sm font-semibold text-white backdrop-blur-md transition hover:bg-purple-500/20 hover:scale-105 active:scale-95 shadow-[0_0_20px_rgba(82,39,255,0.3)]">
            Launch App <ArrowRight className="h-4 w-4" />
          </Link>
        </header>

        <div className="relative z-10 text-center max-w-4xl px-4 pointer-events-none mt-12">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8 }}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-black/40 px-4 py-1.5 text-[11px] font-semibold uppercase tracking-[0.2em] text-purple-200 backdrop-blur-md"
          >
            <Sparkles className="h-3 w-3 text-fuchsia-300" /> State of the Art Context Engine
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="text-5xl md:text-8xl font-black tracking-tighter mb-6 text-transparent bg-clip-text bg-gradient-to-br from-white via-purple-100 to-purple-400/80 filter drop-shadow-[0_0_30px_rgba(82,39,255,0.4)]"
          >
            Intelligence at <br /> Graph Speed
          </motion.h1>

          <BlurText
            text="An agentic context engine with explainable graph memory. Build, traverse, and visualize knowledge graphs that think, explain, and evolve."
            delay={30}
            animateBy="words"
            direction="bottom"
            className="mt-6 text-lg md:text-2xl font-light text-white/80 max-w-2xl mx-auto leading-relaxed"
          />

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1, delay: 1.2 }}
            className="mt-12 pointer-events-auto flex justify-center gap-4"
          >
            <Link to="/chat" className="rounded-full bg-gradient-to-r from-[#5227FF] to-[#B19EEF] px-8 py-4 text-base font-bold text-white shadow-[0_0_40px_-10px_rgba(82,39,255,0.8)] transition hover:scale-105 hover:shadow-[0_0_60px_-10px_rgba(82,39,255,0.9)]">
              Start Traversing
            </Link>
          </motion.div>
        </div>

        <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-[#050110] to-transparent pointer-events-none" />
      </section>

      {/* 2. RICH TYPOGRAPHY (ScrollFloat) */}
      <section id="features" className="py-40 px-4 flex flex-col items-center justify-center text-center bg-[#050110]">
        <ScrollReveal className="max-w-5xl">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.3em] text-purple-400">Graph-Based Memory</p>
          <div className="text-4xl md:text-7xl font-bold tracking-tight text-white leading-tight">
            <ScrollFloat
              animationDuration={1.2}
              ease="back.out(1.5)"
              scrollStart="center bottom+=50%"
              scrollEnd="bottom bottom-=20%"
              stagger={0.03}
            >
              Memory that thinks, explains, and evolves.
            </ScrollFloat>
          </div>
        </ScrollReveal>
      </section>

      {/* 3. FEATURE CARDS (ScrollStack) */}
      <section id="orchestrator" className="py-32 bg-[#050110]">
        <ScrollReveal delay={0.2} className="text-center max-w-4xl mx-auto px-6 mb-20">
          <h2 className="text-5xl font-black text-white mb-6">Three-Layer Memory Architecture</h2>
          <p className="text-xl text-white/50">Personal, Organization, and Global knowledge with explainable reasoning.</p>
        </ScrollReveal>

        <ScrollStack useWindowScroll={true} itemDistance={150} stackPosition="30%">
          <ScrollStackItem>
            <div className="bg-[#0b061d] p-12 md:p-20 rounded-[3rem] border border-purple-500/20 shadow-[0_0_50px_rgba(82,39,255,0.1)] flex flex-col justify-center max-w-5xl mx-auto h-[60vh]">
              <h2 className="text-4xl md:text-6xl font-black mb-6 text-transparent bg-clip-text bg-gradient-to-r from-purple-200 to-fuchsia-300">Personal Memory</h2>
              <p className="text-xl text-white/70 max-w-2xl leading-relaxed">Private user memory isolated per user. Store personal notes, preferences, and private context with full provenance tracking.</p>
            </div>
          </ScrollStackItem>

          <ScrollStackItem>
            <div className="bg-gradient-to-br from-[#120830] to-[#0b061d] p-12 md:p-20 rounded-[3rem] border border-fuchsia-500/20 shadow-[0_0_50px_rgba(255,159,252,0.1)] flex flex-col justify-center max-w-5xl mx-auto h-[60vh]">
              <h2 className="text-4xl md:text-6xl font-black mb-6 text-transparent bg-clip-text bg-gradient-to-r from-fuchsia-200 to-[#FF9FFC]">Organization Memory</h2>
              <p className="text-xl text-white/70 max-w-2xl leading-relaxed">Shared team knowledge scoped to your organization. Collaborate with confidence scoring and automatic conflict detection.</p>
            </div>
          </ScrollStackItem>

          <ScrollStackItem>
            <div className="bg-gradient-to-br from-[#1d0b30] to-[#04010a] p-12 md:p-20 rounded-[3rem] border border-[#5227FF]/30 shadow-[0_0_50px_rgba(82,39,255,0.2)] flex flex-col justify-center max-w-5xl mx-auto h-[60vh]">
              <h2 className="text-4xl md:text-6xl font-black mb-6 text-transparent bg-clip-text bg-gradient-to-r from-white to-[#B19EEF]">Global Memory</h2>
              <p className="text-xl text-white/70 max-w-2xl leading-relaxed">Public world knowledge with write protection. Every relationship stored with reason, timestamp, and confidence score.</p>
            </div>
          </ScrollStackItem>
        </ScrollStack>
      </section>

      {/* 5. HYBRID INTELLIGENCE (Plasma) */}
      <section className="relative w-full py-40 bg-[#050110] flex flex-col items-center justify-center overflow-hidden">
        <div className="absolute inset-0 z-0">
          <Plasma
            color="#5227FF"
            speed={0.5}
            direction="forward"
            scale={1.2}
            opacity={0.8}
            mouseInteractive={true}
          />
        </div>
        <ScrollReveal className="relative z-10 text-center max-w-4xl px-4 pointer-events-none mix-blend-screen">
          <DatabaseZap className="h-16 w-16 mx-auto mb-6 text-fuchsia-300 drop-shadow-[0_0_20px_rgba(255,159,252,0.6)]" />
          <h2 className="text-5xl md:text-7xl font-black text-white mb-6 drop-shadow-2xl">Hybrid Intelligence</h2>
          <p className="text-xl text-purple-100/90 font-medium tracking-wide">
            Graph memory, vector search, and web retrieval working together for complete context assembly.
          </p>
        </ScrollReveal>
      </section>

      {/* 6. GRAPH VISUALIZATION (GridMotion) */}
      <section className="relative w-full h-[80vh] bg-black overflow-hidden flex flex-col items-center justify-center">
        <ScrollReveal className="absolute inset-0 z-0 pointer-events-none">
          <GridMotion gradientColor="#5227FF" items={[]} />
        </ScrollReveal>
        <ScrollReveal className="relative z-10 max-w-3xl text-center px-4 mix-blend-difference pointer-events-none">
          <h2 className="text-5xl md:text-7xl font-black text-white mb-6">Interactive Graph Visualization</h2>
          <p className="text-xl text-white/80">
            Explore knowledge graphs with D3.js. Watch reasoning paths light up in real-time with WebSocket updates.
          </p>
        </ScrollReveal>
      </section>

      {/* 7. CALL TO ACTION & FOOTER (Silk + GradualBlur) */}
      <section className="relative h-[80vh] min-h-[700px] overflow-hidden bg-black">
        <div className="absolute inset-0 z-0 pointer-events-none">
          <Silk
            speed={4}
            scale={1.5}
            color="#5227FF"
            noiseIntensity={1.8}
            rotation={15}
          />
          <div className="absolute inset-0 bg-[#050110]/80 mix-blend-multiply" />
        </div>

        <div className="relative z-10 h-full flex flex-col justify-end pb-32 px-6 pointer-events-none">
          <ScrollReveal className="max-w-4xl mx-auto text-center pointer-events-auto">
            <h2 className="text-5xl md:text-7xl font-black text-white mb-8 drop-shadow-2xl">Ready to build <br />explainable AI?</h2>
            <Link to="/signup" className="inline-flex items-center justify-center rounded-full bg-white px-10 py-5 text-lg font-bold text-purple-950 shadow-[0_0_50px_rgba(255,255,255,0.4)] transition hover:scale-105">
              Get Started Free
            </Link>
          </ScrollReveal>
        </div>

        <footer className="absolute bottom-0 left-0 right-0 z-50 p-6 flex flex-col md:flex-row items-center justify-between border-t border-purple-500/20 bg-black/60 backdrop-blur-md pointer-events-auto">
          <div className="flex items-center gap-2 mb-4 md:mb-0">
            <Network className="h-4 w-4 text-purple-400" />
            <span className="text-sm font-semibold text-white tracking-widest uppercase">NeuroGraph</span>
          </div>
          <div className="text-xs text-white/50 text-center md:text-right font-medium">
            © 2026 NeerajCodz<br />
            Under testing
          </div>
        </footer>
      </section>

    </div>
  );
}

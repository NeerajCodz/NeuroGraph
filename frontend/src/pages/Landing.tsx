import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { BlurText } from '@/components/reactbits/BlurText';
import ScrollFloat from '@/components/text/ScrollFloat';
import Hyperspeed from '@/components/landing/Hyperspeed';
import BorderGlow from '@/components/reactbits/BorderGlow';
import GradientBlinds from '@/components/reactbits/GradientBlinds';
import ArchitectureFlow from '@/components/landing/ArchitectureFlow';
import { ArrowRight, Sparkles } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

// Reusable scroll reveal wrapper
const ScrollReveal = ({ children, className = '', delay = 0 }: { children: React.ReactNode, className?: string, delay?: number }) => (
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
  const { isAuthenticated } = useAuth();

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
                speedUp: 1,
              carLightsFade: 0.6,
              totalSideLightSticks: 10,
              lightPairsPerRoadWay: 20,
              colors: {
                roadColor: 0x120630,
                islandColor: 0x170a3a,
                background: 0x120630,
                shoulderLines: 0x221045,
                brokenLines: 0x221045,
                leftCars: [0x7044ff, 0xa54bf7, 0xb82bf2],
                rightCars: [0x974dff, 0x862cf2, 0x6e1ed9],
                sticks: 0x8a2be2
              }
            }}
          />
        </div>

        {/* Gradient overlay for readability */}
        <div className="absolute inset-0 z-[1] bg-gradient-to-b from-[#050110]/30 via-transparent to-[#050110]" />
        <div className="absolute inset-0 z-[1] bg-[radial-gradient(ellipse_at_center,_transparent_0%,_rgba(5,1,16,0.4)_70%)]" />
        <header className="absolute top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-6 md:px-12 pointer-events-auto">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-600 via-fuchsia-500 to-purple-800 shadow-[0_0_20px_rgba(168,85,247,0.5)] border border-white/20">
              <img src="/logo.svg" alt="NeuroGraph" className="h-6 w-6 brightness-0 invert" />
            </div>
            <span className="text-xl font-bold tracking-tight text-white drop-shadow-md">NeuroGraph</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-purple-100">
            <a href="#features" className="hover:text-white transition">Features</a>
            <a href="#orchestrator" className="hover:text-white transition">Orchestrator</a>
            <a href="#data" className="hover:text-white transition">Logic Flow</a>
          </div>
          <Link
            to={isAuthenticated ? "/chat" : "/login"}
            className="inline-flex items-center justify-center gap-2 px-5 py-2 text-sm font-bold text-white rounded-full transition hover:bg-[#643dff] active:scale-95"
            style={{
              background: '#5227FF',
              boxShadow: 'inset 0 1px 1px rgba(255,255,255,0.28), inset 0 -2px 4px rgba(0,0,0,0.55), 0 0 20px rgba(82,39,255,0.45)',
              borderTop: '0.8px solid rgba(255,255,255,0.35)',
              borderBottom: '1.8px solid rgba(0,0,0,0.65)',
              borderLeft: '1px solid rgba(255,255,255,0.18)',
              borderRight: '1px solid rgba(255,255,255,0.12)',
              textShadow: '0 1px 2px rgba(0,0,0,0.7)'
            }}
          >
            {isAuthenticated ? 'Open' : 'Login'}
            <ArrowRight className="h-4 w-4" />
          </Link>
        </header>

        <div className="relative w-full max-w-7xl mx-auto px-4 lg:px-8 mt-24 z-10 flex justify-center">
          <div className="text-center flex flex-col items-center w-full max-w-4xl mx-auto pointer-events-none">
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
            className="text-5xl md:text-[5rem] lg:text-8xl font-black tracking-tighter mb-6 text-transparent bg-clip-text bg-gradient-to-br from-white via-purple-100 to-purple-400/80 filter drop-shadow-[0_0_30px_rgba(82,39,255,0.4)] text-center"
          >
            Neural-inspired <br />  memory system <br />
          </motion.h1>

          <BlurText
            text="An agentic context engine with explainable graph memory. Build, traverse, and visualize knowledge graphs that think, explain, and evolve."
            delay={30}
            animateBy="words"
            direction="bottom"
            className="mt-6 text-lg md:text-2xl font-light text-white/80 max-w-2xl text-center leading-relaxed"
          />

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1, delay: 1.2 }}
            className="mt-12 pointer-events-auto flex justify-center gap-4"
          >
            <BorderGlow
              className="inline-grid rounded-full"
              borderRadius={999}
              glowRadius={22}
              glowIntensity={1.45}
              edgeSensitivity={10}
              animated={false}
              colors={['#c084fc', '#FF9FFC', '#5227FF']}
            >
              <Link
                to="/chat"
                className="inline-flex items-center justify-center rounded-full px-8 py-4 text-base font-bold text-white transition hover:brightness-110 active:scale-[0.98]"
                style={{
                  background: 'linear-gradient(90deg, #6d3bff 0%, #c054ff 100%)',
                  boxShadow: 'inset 0 2px 3px rgba(255,255,255,0.35), inset 0 -4px 8px rgba(0,0,0,0.65), 0 0 28px rgba(168,85,247,0.45)',
                  borderTop: '1px solid rgba(255,255,255,0.35)',
                  borderBottom: '2px solid rgba(0,0,0,0.75)',
                  borderLeft: '1px solid rgba(255,255,255,0.18)',
                  borderRight: '1px solid rgba(0,0,0,0.35)',
                  textShadow: '0 1px 2px rgba(0,0,0,0.8)',
                }}
              >
                Start Traversing
              </Link>
            </BorderGlow>
          </motion.div>
          </div>
        </div>

        <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-[#050110] to-transparent pointer-events-none" />
      </section>

      {/* 2. RICH TYPOGRAPHY (ScrollFloat) */}
      <section id="features" className="min-h-screen px-4 flex flex-col items-center justify-center text-center bg-[#050110]">
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

      {/* 3. FEATURE CARDS (Simple Reveal Animation) */}
      <section id="orchestrator" className="min-h-screen py-20 bg-[#050110] flex flex-col items-center justify-center">
        <ScrollReveal delay={0.2} className="text-left max-w-4xl mx-auto px-6 mb-20">
          <h2 className="text-5xl font-black text-white mb-6">Three-Layer Memory Architecture</h2>
          <p className="text-xl text-white/50">Personal, Organization, and Global knowledge with explainable reasoning.</p>
        </ScrollReveal>

        <div className="max-w-5xl mx-auto px-4 space-y-12">
          <ScrollReveal delay={0.3}>
            <BorderGlow
              edgeSensitivity={30}
              glowColor="40 80 80"
              backgroundColor="#0b061d"
              borderRadius={48}
              glowRadius={40}
              glowIntensity={1}
              coneSpread={25}
              animated={false}
              colors={['#c084fc', '#f472b6', '#38bdf8']}
            >
              <div className="p-12 md:p-20">
                <h2 className="text-4xl md:text-6xl font-black mb-6 text-transparent bg-clip-text bg-gradient-to-r from-purple-200 to-fuchsia-300">Personal Memory</h2>
                <p className="text-xl text-white/70 max-w-2xl leading-relaxed">Private user memory isolated per user. Store personal notes, preferences, and private context with full provenance tracking.</p>
              </div>
            </BorderGlow>
          </ScrollReveal>

          <ScrollReveal delay={0.4}>
            <BorderGlow
              edgeSensitivity={30}
              glowColor="40 80 80"
              backgroundColor="#120830"
              borderRadius={48}
              glowRadius={40}
              glowIntensity={1}
              coneSpread={25}
              animated={false}
              colors={['#c084fc', '#f472b6', '#38bdf8']}
            >
              <div className="p-12 md:p-20">
                <h2 className="text-4xl md:text-6xl font-black mb-6 text-transparent bg-clip-text bg-gradient-to-r from-fuchsia-200 to-[#FF9FFC]">Organization Memory</h2>
                <p className="text-xl text-white/70 max-w-2xl leading-relaxed">Shared team knowledge scoped to your organization. Collaborate with confidence scoring and automatic conflict detection.</p>
              </div>
            </BorderGlow>
          </ScrollReveal>

          <ScrollReveal delay={0.5}>
            <BorderGlow
              edgeSensitivity={30}
              glowColor="40 80 80"
              backgroundColor="#1d0b30"
              borderRadius={48}
              glowRadius={40}
              glowIntensity={1}
              coneSpread={25}
              animated={false}
              colors={['#c084fc', '#f472b6', '#38bdf8']}
            >
              <div className="p-12 md:p-20">
                <h2 className="text-4xl md:text-6xl font-black mb-6 text-transparent bg-clip-text bg-gradient-to-r from-white to-[#B19EEF]">Global Memory</h2>
                <p className="text-xl text-white/70 max-w-2xl leading-relaxed">Public world knowledge with write protection. Every relationship stored with reason, timestamp, and confidence score.</p>
              </div>
            </BorderGlow>
          </ScrollReveal>
        </div>
      </section>

      <section id="data" className="min-h-screen py-20 bg-[#050110] flex flex-col items-center justify-center relative border-t border-white/5">
        <ScrollReveal className="max-w-5xl w-full px-4">
          <p className="text-center mb-4 text-sm font-semibold uppercase tracking-[0.3em] text-purple-400">Architecture Flow</p>
          <div className="text-center text-4xl md:text-5xl font-bold tracking-tight text-white mb-12">
            The Processing Engine
          </div>
          
          <div className="rounded-[40px] border border-white/10 bg-black/40 backdrop-blur-md p-6 md:p-12 overflow-hidden shadow-[0_0_80px_-20px_rgba(82,39,255,0.4)] relative">
            {/* Flowchart Diagram */}
            <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_center,_rgba(82,39,255,0.15)_0%,_transparent_70%)]" />
            <div className="relative z-10 w-full overflow-x-auto overflow-y-hidden">
              <ArchitectureFlow />
            </div>
          </div>
        </ScrollReveal>
      </section>

      
      {/* 5. HYBRID INTELLIGENCE (GridMotion Graph Memory) */}
      <section className="relative w-full min-h-screen bg-[#050110] flex flex-col items-center justify-center overflow-hidden border-t border-white/5">
        <ScrollReveal className="relative z-10 text-center max-w-5xl px-4 pointer-events-none pb-20">
          <h2 className="text-5xl md:text-7xl font-black text-white mb-6 drop-shadow-[0_0_80px_rgba(255,159,252,0.8)]">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-fuchsia-400 to-purple-600">Hyper Intelligence</span>
          </h2>
          <p className="text-2xl text-purple-100/90 font-medium tracking-wide max-w-3xl mx-auto mb-14 drop-shadow-lg">
            An Agentic Context Engine with Explainable Graph Memory
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-left max-w-4xl mx-auto pointer-events-auto relative mt-12">
            
            <div className="absolute inset-0 bg-fuchsia-500/10 blur-[80px] -z-10 rounded-full" />
            
            <div className="p-8 rounded-3xl bg-black/60 border border-fuchsia-500/30 backdrop-blur-xl hover:bg-black/40 transition-all hover:scale-[1.02] shadow-[0_0_40px_rgba(168,85,247,0.2)]">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 shrink-0 rounded-xl flex items-center justify-center bg-gradient-to-br from-purple-600 via-fuchsia-500 to-purple-800 shadow-[0_0_25px_rgba(168,85,247,0.5)] border border-white/20 p-2.5">
                  <img src="/logo.svg" alt="NeuroGraph" className="w-full h-full brightness-0 invert drop-shadow-[0_0_6px_rgba(255,255,255,0.5)]" />
                </div>
                <h3 className="text-2xl font-bold text-white">Three-Layer Graph</h3>
              </div>
              <p className="text-purple-100/80 leading-relaxed text-base pt-2">
                Unlike traditional RAG systems, NeuroGraph actively builds dynamic context across <strong className="text-purple-300">Personal</strong>, <strong className="text-purple-300">Organization</strong>, and <strong className="text-purple-300">Global</strong> write-protected layers. Every fact is a semantically linked node, not just a document chunk.
              </p>
            </div>
            
            <div className="p-8 rounded-3xl bg-black/60 border border-purple-500/30 backdrop-blur-xl hover:bg-black/40 transition-all hover:scale-[1.02] shadow-[0_0_40px_rgba(168,85,247,0.2)]">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 rounded-xl bg-fuchsia-500/20 flex items-center justify-center border border-fuchsia-500/30">
                  <Sparkles className="w-6 h-6 text-fuchsia-300" />
                </div>
                <h3 className="text-2xl font-bold text-white">Explainable Reasoning</h3>
              </div>
              <p className="text-purple-100/80 leading-relaxed text-base pt-2">
                Every relationship is stored with reason, timestamp, and a confidence score. This creates traceable reasoning paths and enables temporal decay degradation over time with full provenance tracking.
              </p>
            </div>
          </div>
        </ScrollReveal>
      </section>
{/* 7. CALL TO ACTION & FOOTER (GradientBlinds + Liquid Glass Buttons) */}
      <section className="relative min-h-screen overflow-hidden bg-[#050110]">
        <div className="absolute inset-0 z-0 pointer-events-none">
          <GradientBlinds
            className="w-full h-full"
            dpr={2}
            gradientColors={['#050110', '#0a031d', '#14072c', '#26104b', '#3a1b65']}
            angle={-18}
            noise={0.1}
            blindCount={24}
            blindMinWidth={42}
            mouseDampening={0.12}
            mirrorGradient
            spotlightRadius={0.62}
            spotlightSoftness={1.25}
            spotlightOpacity={0.35}
            distortAmount={0.22}
            shineDirection="right"
            mixBlendMode="normal"
          />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(82,39,255,0.16)_0%,_rgba(255,159,252,0.07)_30%,_rgba(5,1,16,0.94)_72%)]" />
          <div className="absolute inset-0 bg-black/35" />
        </div>

        <div className="relative z-10 min-h-screen flex items-center justify-center px-6 pointer-events-none">
          <ScrollReveal className="max-w-4xl mx-auto text-center pointer-events-auto">
            <p className="mb-4 text-xs md:text-sm font-semibold uppercase tracking-[0.28em] text-purple-200/80">
              Your Context Engine Starts Here
            </p>
            <h2 className="text-5xl md:text-7xl font-black text-white mb-6 drop-shadow-[0_0_30px_rgba(177,158,239,0.35)]">
              Ready to build <br />explainable AI?
            </h2>
            <p className="mx-auto mb-10 max-w-2xl text-lg text-purple-100/80 leading-relaxed">
              Ship memory-first agents with transparent reasoning, layered knowledge scopes, and a visual graph that your team can trust.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/signup" className="liquid-glass-btn liquid-glass-btn--primary">
                Get Started Free <ArrowRight className="h-4 w-4" />
              </Link>
              <BorderGlow
                className="inline-grid rounded-full"
                edgeSensitivity={28}
                glowColor="40 80 80"
                backgroundColor="rgba(10, 4, 24, 0.8)"
                borderRadius={999}
                glowRadius={30}
                glowIntensity={1}
                coneSpread={20}
                animated={false}
                colors={['#B19EEF', '#FF9FFC', '#38bdf8']}
              >
                <Link to="/chat" className="liquid-glass-btn liquid-glass-btn--theme">
                  Launch App
                </Link>
              </BorderGlow>
            </div>
          </ScrollReveal>
        </div>

        <footer className="absolute bottom-0 left-0 right-0 z-50 p-6 flex flex-col md:flex-row items-center justify-between border-t border-purple-500/20 bg-black/40 backdrop-blur-md pointer-events-auto">
          <div className="flex items-center gap-2 mb-4 md:mb-0">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-purple-600 via-fuchsia-500 to-purple-800 shadow-[0_0_15px_rgba(168,85,247,0.4)] border border-white/20 p-1.5">
              <img src="/logo.svg" alt="NeuroGraph" className="w-full h-full brightness-0 invert drop-shadow-[0_0_4px_rgba(255,255,255,0.4)]" />
            </div>
            <span className="text-sm font-bold text-white tracking-widest uppercase drop-shadow-sm">NeuroGraph</span>
          </div>
          <div className="text-xs text-white/50 text-center md:text-right font-medium">
            © 2026{' '}
            <a
              href="https://github.com/NeerajCodz/NeuroGraph"
              target="_blank"
              rel="noreferrer"
              className="text-purple-200/90 hover:text-white underline underline-offset-2 transition"
            >
              NeerajCodz/NeuroGraph
            </a>
          </div>
        </footer>
      </section>

    </div>
  );
}



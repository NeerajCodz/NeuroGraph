import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { BlurText } from '@/components/reactbits/BlurText';
import ScrollFloat from '@/components/text/ScrollFloat';
import Hyperspeed from '@/components/landing/Hyperspeed';
import BorderGlow from '@/components/BorderGlow';
import ShapeBlur from '@/components/ShapeBlur';
import Iridescence from '@/components/Iridescence';
import GradientBlinds from '@/components/GradientBlinds';
import ArchitectureFlow from '@/components/landing/ArchitectureFlow';
import { ArrowRight, Network, Sparkles, DatabaseZap } from 'lucide-react';

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
                roadColor: 0x050110,
                islandColor: 0x070215,
                background: 0x050110,
                shoulderLines: 0x0b0520,
                brokenLines: 0x0b0520,
                leftCars: [0x5227ff, 0x8a2be2, 0x9400d3],
                rightCars: [0x7b2cbf, 0x6a0dad, 0x4b0082],
                sticks: 0x5a189a
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
            Neural-inspired <br />  memory system <br />
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
        <ScrollReveal delay={0.2} className="text-center max-w-4xl mx-auto px-6 mb-20">
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

      {/* 5. HYBRID INTELLIGENCE (Iridescence + ShapeBlur) */}
      <section className="relative w-full min-h-screen bg-[#050110] flex flex-col items-center justify-center overflow-hidden">
        <div className="absolute inset-0 z-0">
          <Iridescence
            color={[0.5, 0.6, 0.8]}
            mouseReact
            amplitude={0.1}
            speed={1}
          />
        </div>
        <div className="absolute inset-0 z-[1] bg-[radial-gradient(ellipse_at_top,_rgba(177,158,239,0.26)_0%,_rgba(82,39,255,0.12)_35%,_rgba(5,1,16,0.92)_78%)]" />
        <div className="absolute z-[2] h-[520px] w-[520px] -left-20 top-1/2 -translate-y-1/2 opacity-60 pointer-events-none">
          <ShapeBlur
            variation={2}
            shapeSize={1.2}
            roundness={0.5}
            borderSize={0.045}
            circleSize={0.28}
            circleEdge={0.45}
          />
        </div>
        <div className="absolute z-[2] h-[420px] w-[420px] -right-10 bottom-10 opacity-45 pointer-events-none">
          <ShapeBlur
            variation={0}
            shapeSize={1.0}
            roundness={0.42}
            borderSize={0.055}
            circleSize={0.24}
            circleEdge={0.55}
          />
        </div>
        <ScrollReveal className="relative z-10 text-center max-w-4xl px-4 pointer-events-none">
          <DatabaseZap className="h-16 w-16 mx-auto mb-6 text-fuchsia-300 drop-shadow-[0_0_20px_rgba(255,159,252,0.6)]" />
          <h2 className="text-5xl md:text-7xl font-black text-white mb-6 drop-shadow-2xl">Hyper Intelligence</h2>
          <p className="text-xl text-purple-100/90 font-medium tracking-wide">
            Graph memory, vector search, and web retrieval working together for complete context assembly.
          </p>
        </ScrollReveal>
      </section>

      {/* 7. CALL TO ACTION & FOOTER (GradientBlinds + Liquid Glass Buttons) */}
      <section className="relative min-h-screen overflow-hidden bg-[#050110]">
        <div className="absolute inset-0 z-0 pointer-events-none">
          <GradientBlinds
            className="w-full h-full"
            dpr={2}
            gradientColors={['#080214', '#1b0f38', '#5227FF', '#B19EEF', '#FF9FFC']}
            angle={-18}
            noise={0.2}
            blindCount={24}
            blindMinWidth={42}
            mouseDampening={0.12}
            mirrorGradient
            spotlightRadius={0.62}
            spotlightSoftness={1.25}
            spotlightOpacity={0.8}
            distortAmount={0.45}
            shineDirection="right"
            mixBlendMode="screen"
          />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(82,39,255,0.22)_0%,_rgba(255,159,252,0.12)_32%,_rgba(5,1,16,0.9)_74%)]" />
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

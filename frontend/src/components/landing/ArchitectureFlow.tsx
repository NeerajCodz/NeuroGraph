import React from 'react';
import { motion } from 'framer-motion';
import BorderGlow from '@/components/BorderGlow';
import { MessageSquare, Terminal, Webhook, Bot, Server, Activity, Brain, Layers, Globe, Download, ShieldAlert, Bell, Network, Database, Container } from 'lucide-react';

const FlowNode = ({ icon: Icon, title, subtitle, popup, delay = 0, colorClass = "from-purple-500/20 to-purple-500/0", borderClass = "border-purple-500/30" }: { icon: React.ComponentType<{ className?: string }>, title: string, subtitle: string, popup: string, delay?: number, colorClass?: string, borderClass?: string }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: "-50px" }}
    transition={{ delay, duration: 0.5 }}
    className="relative group cursor-pointer z-10 w-full"
  >
    <div className={`flex flex-col items-center justify-center text-center p-4 rounded-xl border ${borderClass} bg-gradient-to-b ${colorClass} backdrop-blur-sm transition-all hover:scale-105 hover:shadow-[0_0_20px_rgba(168,85,247,0.3)]`}>
      <Icon className="w-8 h-8 mb-3 text-purple-300 group-hover:text-purple-200 transition-colors" />
      <h4 className="text-sm font-bold text-white whitespace-nowrap">{title}</h4>
      <p className="text-[11px] text-white/60 whitespace-nowrap mt-1">{subtitle}</p>
    </div>
    
    {/* Pop-up info layer */}
    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-56 p-3 bg-black/90 border border-purple-500/50 rounded-xl text-xs text-purple-100 opacity-0 group-hover:opacity-100 transition-all duration-300 pointer-events-none z-50 shadow-[0_10px_30px_rgba(0,0,0,0.8)] scale-95 group-hover:scale-100 origin-bottom after:content-[''] after:absolute after:top-full after:left-1/2 after:-translate-x-1/2 after:border-solid after:border-t-purple-500/50 after:border-t-8 after:border-x-transparent after:border-x-8 after:border-b-0">
      {popup}
    </div>
  </motion.div>
);

const FlowLayer = ({ title, children, delay = 0 }: { title: string, children: React.ReactNode, delay?: number }) => (
  <motion.div 
    initial={{ opacity: 0 }}
    whileInView={{ opacity: 1 }}
    viewport={{ once: true, margin: "-50px" }}
    transition={{ delay: delay, duration: 0.8 }}
    className="flex flex-col items-center w-full my-4"
  >
    <h3 className="text-[11px] font-bold uppercase tracking-[0.25em] text-purple-400 mb-6 bg-purple-500/10 px-4 py-1.5 rounded-full border border-purple-500/20">{title}</h3>
    <div className="flex flex-wrap justify-center gap-4 w-full">
      {children}
    </div>
  </motion.div>
);

const AnimatedArrow = ({ delay = 0 }: { delay?: number }) => (
  <motion.div
    initial={{ opacity: 0, height: 0 }}
    whileInView={{ opacity: 1, height: 40 }}
    viewport={{ once: true, margin: "-50px" }}
    transition={{ delay, duration: 0.5 }}
    className="w-px bg-gradient-to-b from-purple-500/50 via-purple-400/80 to-purple-500/10 mx-auto my-2"
  >
    {/* Arrow head indicator */}
    <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 border-b border-r border-purple-400/80 rotate-45 transform"></div>
  </motion.div>
);

export default function ArchitectureFlow() {
  return (
    <div className="w-full relative py-10 flex flex-col items-center">
        
        {/* === User Interfaces Layer === */}
        <FlowLayer title="I. Ingestion Layer" delay={0.1}>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 w-full max-w-3xl">
                <FlowNode icon={MessageSquare} title="Chat UI" subtitle="React + Vite" popup="Main web interface for standard users to query the context engine directly." delay={0.2} colorClass="from-blue-500/20 to-blue-500/0" borderClass="border-blue-500/30" />
                <FlowNode icon={Terminal} title="MCP Clients" subtitle="Claude, Cursor" popup="Direct IDE/Agent integration using Model Context Protocol." delay={0.3} />
                <FlowNode icon={Webhook} title="Webhooks" subtitle="Slack, GitHub" popup="Asynchronous event ingestion from third-party services and pipelines." delay={0.4} colorClass="from-pink-500/20 to-pink-500/0" borderClass="border-pink-500/30" />
            </div>
        </FlowLayer>

        <AnimatedArrow delay={0.6} />

        {/* === Processing Layer === */}
        <FlowLayer title="II. Processing Engine" delay={0.7}>
            <BorderGlow className="w-full max-w-4xl" borderRadius={24} edgeSensitivity={40} glowColor="270 80 60" glowRadius={60} glowIntensity={0.8} coneSpread={30}>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 p-6 bg-black/60 backdrop-blur-xl rounded-[24px]">
                    <FlowNode icon={Bot} title="Orchestrator" subtitle="Groq/Llama 3.3" popup="Master intelligence that routes queries to appropriate sub-agents or processing pipelines." delay={0.8} />
                    <FlowNode icon={Server} title="MCP Router" subtitle="FastAPI Core" popup="Direct pipeline executing Context Builder operations instantly for automated clients." delay={0.9} colorClass="from-violet-500/30 to-violet-500/0" borderClass="border-violet-500/40" />
                    <FlowNode icon={Activity} title="Event Bus" subtitle="Asynchronous Queue" popup="A resilient decoupled transport layer separating ingestion from heavy agent operations." delay={1.0} colorClass="from-[rgb(244,114,182)]/20 to-[rgb(244,114,182)]/0" borderClass="border-[rgb(244,114,182)]/30" />
                </div>
            </BorderGlow>
        </FlowLayer>

        <AnimatedArrow delay={1.2} />

        {/* === Agent Layer === */}
        <FlowLayer title="III. Agent Swarm" delay={1.3}>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 w-full max-w-[1200px]">
                <FlowNode icon={Brain} title="Memory" subtitle="Manager" popup="Controls life-cycle of graph nodes, entity creation, and executing CRUD." delay={1.4} />
                <FlowNode icon={Layers} title="Context" subtitle="Builder" popup="Assembles deep subgraphs into localized prompts for the Orchestrator." delay={1.5} colorClass="from-indigo-500/20 to-indigo-500/0" borderClass="border-indigo-500/30" />
                <FlowNode icon={Globe} title="Web Surfer" subtitle="Tavily Tools" popup="Navigates the web to gather recent external context when internal context is missing." delay={1.6} />
                <FlowNode icon={Download} title="Importer" subtitle="Batch Worker" popup="Processes massive code repositories and offline documents via embeddings." delay={1.7} colorClass="from-fuchsia-500/20 to-fuchsia-500/0" borderClass="border-fuchsia-500/30" />
                <FlowNode icon={ShieldAlert} title="Conflict" subtitle="Resolver" popup="Scans the graph structure post-ingestion to mitigate conflicting knowledge." delay={1.8} />
                <FlowNode icon={Bell} title="Reminder" subtitle="Agent" popup="Continuously monitors time-bound tasks and injects temporal alerts into sessions." delay={1.9} />
            </div>
        </FlowLayer>

        <AnimatedArrow delay={2.1} />

        {/* === Data Layer === */}
        <FlowLayer title="IV. Persistence" delay={2.2}>
           <BorderGlow className="w-full max-w-3xl" borderRadius={24} edgeSensitivity={40} glowColor="200 80 50" glowRadius={60} glowIntensity={0.8} coneSpread={30}>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 p-6 bg-black/60 backdrop-blur-xl rounded-[24px]">
                    <FlowNode icon={Network} title="Neo4j Layer" subtitle="Semantic Graph" popup="Primary source of truth for semantic relationships and interconnected nodes." delay={2.3} colorClass="from-blue-400/20 to-blue-400/0" borderClass="border-blue-400/30" />
                    <FlowNode icon={Database} title="pgvector" subtitle="Embeddings" popup="Used for rapid dense semantic similarity searches to prime graph retrievers." delay={2.4} colorClass="from-cyan-400/20 to-cyan-400/0" borderClass="border-cyan-400/30" />
                    <FlowNode icon={Container} title="Redis Cache" subtitle="Upstash Queue" popup="Lightning fast volatile storage for conversation sessions and background tasks." delay={2.5} colorClass="from-[rgb(239,68,68)]/20 to-[rgb(239,68,68)]/0" borderClass="border-[rgb(239,68,68)]/30" />
                </div>
            </BorderGlow>
        </FlowLayer>

    </div>
  )
}

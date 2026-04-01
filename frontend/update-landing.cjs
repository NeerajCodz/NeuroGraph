const fs = require('fs');
let code = fs.readFileSync('src/pages/Landing.tsx', 'utf8');

if (!code.includes('import GridMotion')) {
    code = code.replace(/import \{ Link \} from 'react-router-dom';/, "import { Link } from 'react-router-dom';\nimport GridMotion from '@/components/landing/GridMotion';");
}

const newSection = `
      {/* 5. HYBRID INTELLIGENCE (GridMotion Graph Memory) */}
      <section className="relative w-full min-h-screen bg-[#050110] flex flex-col items-center justify-center overflow-hidden border-t border-white/5">
        <div className="absolute inset-0 z-0 pointer-events-none opacity-50 text-[10px]">
          <GridMotion
            gradientColor="#050110"
            items={[
              'Entity', 'Relationship', 'Node', 'Edge',
              'Provenance', 'Timestamp', 'Confidence', 'Layer',
              'Vector', 'Embedding', 'Similarity', 'Context',
              'Reasoning', 'Memory', 'Knowledge', 'Graph',
              'Temporal Decay', 'Traverse', 'Connect', 'Discover',
              'Personal', 'Organization', 'Global', 'Hybrid',
              'Explain', 'Source', 'Score', 'Path'
            ]}
          />
        </div>
        <div className="absolute inset-0 z-[1] bg-[radial-gradient(ellipse_at_center,_rgba(5,1,16,0.3)_0%,_rgba(5,1,16,0.95)_50%)] pointer-events-none" />
        
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
                <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center border border-purple-500/30">
                  <Network className="w-6 h-6 text-purple-300" />
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
`;

code = code.replace(/\{\/\* 5\. HYBRID INTELLIGENCE[\s\S]*?(?=\{\/\* 7\. CALL TO ACTION)/, newSection);

fs.writeFileSync('src/pages/Landing.tsx', code);

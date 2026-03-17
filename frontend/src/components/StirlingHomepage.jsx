import { 
  Bot, Brain, Database, Shield, Zap, Server, 
  Code, MessageSquare, GitBranch, Globe, Cpu, 
  ChevronRight, Sparkles, Layout, Lock, Search,
  Users, BarChart, Workflow, Layers, Network,
  ArrowRight, ExternalLink, Linkedin, Mail
} from 'lucide-react'

// Logo image - using the University logo as requested
const IMAGES = {
  logo: '/images/stirling-logo.svg',
}

// Key project metrics
const STATS = [
  { value: '1,206', label: 'University Pages Scraped', icon: Globe },
  { value: '15,000+', label: 'Text Chunks Processed', icon: Layers },
  { value: '1,536', label: 'Vector Dimensions', icon: Network },
  { value: '3', label: 'AI Agents Orchestrated', icon: Workflow },
]

// Tech stack categories
const TECH_STACK = [
  {
    category: 'AI & ML',
    icon: Brain,
    items: [
      { name: 'Claude 3 Haiku', desc: 'Anthropic LLM for conversational AI' },
      { name: 'OpenAI Embeddings', desc: 'text-embedding-3-small (1,536D)' },
      { name: 'LangGraph', desc: '3-agent state machine orchestration' },
    ]
  },
  {
    category: 'Search & RAG',
    icon: Search,
    items: [
      { name: 'Hybrid RAG', desc: 'Vector similarity + BM25 keyword search' },
      { name: 'Re-ranking', desc: 'Cross-encoder relevance scoring' },
      { name: 'pgvector', desc: 'PostgreSQL vector similarity search' },
    ]
  },
  {
    category: 'Safety & Guardrails',
    icon: Shield,
    items: [
      { name: 'Topic Boundaries', desc: 'University-focused scope enforcement' },
      { name: 'Prompt Injection Guard', desc: 'Multi-layer security filters' },
      { name: 'Safety Monitoring', desc: 'Incident logging & rate limiting' },
    ]
  },
  {
    category: 'Backend & API',
    icon: Server,
    items: [
      { name: 'FastAPI', desc: 'High-performance Python REST API' },
      { name: 'PostgreSQL', desc: '13 tables, 30+ optimized indexes' },
      { name: '7 Endpoints', desc: 'Chat, feedback, health & analytics' },
    ]
  },
  {
    category: 'Frontend & UI',
    icon: Layout,
    items: [
      { name: 'React 18', desc: 'Modern component-based architecture' },
      { name: 'TailwindCSS', desc: 'Utility-first responsive styling' },
      { name: 'Vite Build', desc: 'Lightning-fast development & build' },
    ]
  },
  {
    category: 'Data Pipeline',
    icon: GitBranch,
    items: [
      { name: 'FireCrawl', desc: 'JS-rendered web scraping engine' },
      { name: 'Smart Chunking', desc: 'Semantic text segmentation' },
      { name: 'Lead Capture', desc: 'Progressive data collection system' },
    ]
  },
]

// Architecture flow steps
const ARCHITECTURE_STEPS = [
  {
    title: 'Router Agent',
    desc: 'Intent classification & query routing',
    icon: Bot,
    color: 'from-blue-500 to-blue-600'
  },
  {
    title: 'RAG Agent',
    desc: 'Hybrid retrieval & context synthesis',
    icon: Database,
    color: 'from-emerald-500 to-emerald-600'
  },
  {
    title: 'Lead Agent',
    desc: 'Progressive data capture & tracking',
    icon: Users,
    color: 'from-purple-500 to-purple-600'
  },
]

export default function StirlingHomepage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100" style={{ fontFamily: "'Inter', 'Open Sans', system-ui, sans-serif" }}>
      
      {/* Navigation Bar */}
      <nav className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-slate-200/60">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <a href="https://www.stir.ac.uk/" className="flex items-center gap-3 group">
              <img 
                src={IMAGES.logo}
                alt="University of Stirling" 
                className="h-10 md:h-12 transition-transform group-hover:scale-105"
              />
              <span className="text-slate-600 text-sm font-medium hidden sm:block">Research Project</span>
            </a>
            
            <div className="flex items-center gap-6">
              <span className="text-slate-500 text-sm hidden md:block">Built by</span>
              <div className="flex items-center gap-3">
                <span className="font-semibold text-slate-800">Baqar Jafri</span>
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center text-white text-sm font-bold">
                  BJ
                </div>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
        </div>
        
        <div className="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-12">
          {/* Badge */}
          <div className="flex justify-center mb-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gradient-to-r from-emerald-50 to-blue-50 border border-emerald-200/60">
              <Sparkles className="w-4 h-4 text-emerald-600" />
              <span className="text-sm font-medium text-emerald-800">AI-Powered Research Project</span>
            </div>
          </div>
          
          {/* Main Title */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-center text-slate-900 mb-6 leading-tight">
            Stirling University
            <span className="block bg-gradient-to-r from-emerald-600 to-blue-600 bg-clip-text text-transparent">
              AI Chat Assistant
            </span>
          </h1>
          
          {/* Subtitle */}
          <p className="text-lg sm:text-xl text-center text-slate-600 max-w-3xl mx-auto mb-10 leading-relaxed">
            An enterprise-grade conversational AI system built with Retrieval-Augmented Generation (RAG), 
            multi-agent orchestration, and advanced safety guardrails for prospective student engagement.
          </p>
          
          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <button 
              onClick={() => window.dispatchEvent(new CustomEvent('openChatWidget'))}
              className="group inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/25 hover:shadow-emerald-500/40 hover:scale-105 transition-all duration-300"
            >
              <MessageSquare className="w-5 h-5" />
              Try the AI Chat
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
          
          {/* Key Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
            {STATS.map((stat, idx) => (
              <div 
                key={idx} 
                className="bg-white/60 backdrop-blur-sm rounded-2xl p-5 border border-slate-200/60 hover:border-emerald-300/60 hover:shadow-lg hover:shadow-emerald-500/5 transition-all duration-300"
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500/10 to-blue-500/10">
                    <stat.icon className="w-5 h-5 text-emerald-600" />
                  </div>
                  <span className="text-2xl sm:text-3xl font-bold text-slate-900">{stat.value}</span>
                </div>
                <p className="text-sm text-slate-600">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Architecture Section */}
      <section className="py-16 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 mb-4">
              <Workflow className="w-5 h-5 text-emerald-600" />
              <span className="text-sm font-semibold text-emerald-600 uppercase tracking-wide">System Architecture</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
              3-Agent LangGraph Orchestration
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              A sophisticated state machine that routes queries through specialized AI agents, 
              each optimized for different stages of the conversation pipeline.
            </p>
          </div>
          
          {/* Architecture Flow */}
          <div className="relative">
            {/* Connection Lines (Desktop) */}
            <div className="hidden md:block absolute top-1/2 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-200 via-emerald-200 to-purple-200 -translate-y-1/2" />
            
            <div className="grid md:grid-cols-3 gap-6 md:gap-8 relative z-10">
              {ARCHITECTURE_STEPS.map((step, idx) => (
                <div 
                  key={idx}
                  className="group bg-gradient-to-br from-slate-50 to-white rounded-2xl p-6 border border-slate-200 hover:border-emerald-300/60 hover:shadow-xl hover:shadow-emerald-500/10 transition-all duration-300"
                >
                  <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${step.color} flex items-center justify-center text-white shadow-lg mb-4 group-hover:scale-110 transition-transform duration-300`}>
                    <step.icon className="w-7 h-7" />
                  </div>
                  <div className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-slate-100 text-slate-600 font-bold text-sm mb-3">
                    {idx + 1}
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">{step.title}</h3>
                  <p className="text-slate-600">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>
          
          {/* Architecture Diagram Text */}
          <div className="mt-10 p-6 bg-slate-50 rounded-2xl border border-slate-200">
            <div className="flex flex-wrap items-center justify-center gap-2 text-sm font-medium text-slate-700">
              <span className="px-3 py-1.5 bg-white rounded-lg border border-slate-200">React Frontend</span>
              <ChevronRight className="w-4 h-4 text-slate-400" />
              <span className="px-3 py-1.5 bg-white rounded-lg border border-slate-200">FastAPI Backend</span>
              <ChevronRight className="w-4 h-4 text-slate-400" />
              <span className="px-3 py-1.5 bg-blue-50 rounded-lg border border-blue-200 text-blue-700">Router Agent</span>
              <ChevronRight className="w-4 h-4 text-slate-400" />
              <span className="px-3 py-1.5 bg-emerald-50 rounded-lg border border-emerald-200 text-emerald-700">RAG Agent</span>
              <ChevronRight className="w-4 h-4 text-slate-400" />
              <span className="px-3 py-1.5 bg-purple-50 rounded-lg border border-purple-200 text-purple-700">Lead Capture</span>
              <ChevronRight className="w-4 h-4 text-slate-400" />
              <span className="px-3 py-1.5 bg-slate-700 text-white rounded-lg">PostgreSQL + pgvector</span>
            </div>
          </div>
        </div>
      </section>

      {/* Tech Stack Grid */}
      <section className="py-16 bg-gradient-to-b from-slate-50 to-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 mb-4">
              <Cpu className="w-5 h-5 text-emerald-600" />
              <span className="text-sm font-semibold text-emerald-600 uppercase tracking-wide">Technology Stack</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
              Enterprise-Grade Technology
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Built with production-ready technologies chosen for performance, scalability, and reliability.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {TECH_STACK.map((category, idx) => (
              <div 
                key={idx}
                className="group bg-white rounded-2xl p-6 border border-slate-200 hover:border-emerald-300/60 hover:shadow-xl hover:shadow-emerald-500/5 transition-all duration-300"
              >
                <div className="flex items-center gap-3 mb-5">
                  <div className="p-2.5 rounded-xl bg-gradient-to-br from-emerald-500/10 to-blue-500/10 group-hover:from-emerald-500/20 group-hover:to-blue-500/20 transition-colors">
                    <category.icon className="w-6 h-6 text-emerald-600" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-900">{category.category}</h3>
                </div>
                
                <div className="space-y-4">
                  {category.items.map((item, itemIdx) => (
                    <div key={itemIdx} className="border-l-2 border-slate-200 pl-4 hover:border-emerald-400 transition-colors">
                      <p className="font-semibold text-slate-800 text-sm">{item.name}</p>
                      <p className="text-xs text-slate-500 mt-0.5">{item.desc}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Key Features / Expertise Section */}
      <section className="py-16 bg-white">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 mb-4">
              <Zap className="w-5 h-5 text-emerald-600" />
              <span className="text-sm font-semibold text-emerald-600 uppercase tracking-wide">Core Capabilities</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
              Advanced AI Implementation
            </h2>
          </div>
          
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                icon: Database,
                title: 'Hybrid RAG System',
                desc: 'Combines vector similarity search with BM25 keyword matching for superior retrieval accuracy'
              },
              {
                icon: Shield,
                title: 'Multi-Layer Safety',
                desc: 'Topic boundaries, prompt injection detection, and comprehensive guardrail system'
              },
              {
                icon: Users,
                title: 'Progressive Lead Capture',
                desc: 'Intelligent data collection that tracks user journey and optimizes conversion'
              },
              {
                icon: BarChart,
                title: 'Feedback Analytics',
                desc: '3-level rating system with sentiment analysis and improvement tracking'
              },
            ].map((feature, idx) => (
              <div 
                key={idx}
                className="group p-6 rounded-2xl bg-slate-50 border border-slate-200 hover:bg-white hover:border-emerald-300/60 hover:shadow-xl hover:shadow-emerald-500/5 transition-all duration-300"
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center text-white mb-4 group-hover:scale-110 transition-transform">
                  <feature.icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">{feature.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Developer Profile Section */}
      <section className="py-16 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 mb-6">
            <Code className="w-5 h-5 text-emerald-400" />
            <span className="text-sm font-semibold text-emerald-400 uppercase tracking-wide">About the Developer</span>
          </div>
          
          <h2 className="text-3xl sm:text-4xl font-bold mb-6">
            Advanced Expertise in AI Solutions
          </h2>
          
          <p className="text-lg text-slate-300 leading-relaxed mb-8 max-w-3xl mx-auto">
            This project demonstrates comprehensive knowledge of modern AI system architecture, 
            including LLM orchestration, vector databases, RAG pipelines, safety engineering, 
            and production deployment patterns. Built as a research initiative to explore 
            the capabilities of conversational AI in educational contexts.
          </p>
          
          <div className="flex flex-wrap items-center justify-center gap-4">
            <a 
              href="https://www.linkedin.com/in/thebaqarjafri/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
            >
              <Linkedin className="w-5 h-5" />
              <span className="font-medium">LinkedIn</span>
            </a>
            <a 
              href="mailto:contact@example.com" 
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors"
            >
              <Mail className="w-5 h-5" />
              <span className="font-medium">Get in Touch</span>
            </a>
          </div>
        </div>
      </section>

      {/* Chat CTA Section */}
      <section className="py-16 bg-gradient-to-r from-emerald-600 to-emerald-700">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Experience the AI Chat
          </h2>
          <p className="text-lg text-emerald-100 mb-8 max-w-2xl mx-auto">
            Ask about courses, entry requirements, campus life, or anything about studying at the University of Stirling. 
            The AI will provide accurate, contextual responses using the RAG system.
          </p>
          <button 
            onClick={() => window.dispatchEvent(new CustomEvent('openChatWidget'))}
            className="group inline-flex items-center gap-3 px-8 py-4 bg-white text-emerald-700 font-bold rounded-xl shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300"
          >
            <MessageSquare className="w-6 h-6" />
            Start Chatting Now
            <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </section>

      {/* Simple Footer */}
      <footer className="bg-slate-900 text-slate-400 py-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <img 
                src={IMAGES.logo}
                alt="University of Stirling" 
                className="h-8 opacity-60"
              />
              <span className="text-sm">Independent Research Project</span>
            </div>
            <p className="text-sm">
              Built with React, FastAPI, LangGraph & Claude AI
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

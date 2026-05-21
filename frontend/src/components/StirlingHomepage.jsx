import { 
  Bot, Brain, Database, Shield, Zap, Server, 
  MessageSquare, GitBranch, Globe, Cpu, 
  ChevronRight, Sparkles, Layout, Search,
  Users, BarChart, Workflow, Layers, Network,
  ArrowRight, Linkedin, Mail, BookOpen, Link2,
  MessageCircle, ListChecks, GraduationCap, Maximize2
} from 'lucide-react'

const IMAGES = {
  logo: '/images/stirling-logo.svg',
}

const NAV_LINKS = [
  { href: '#chat-features', label: 'Chat features' },
  { href: '#how-it-works', label: 'How it works' },
  { href: '#technology', label: 'Technology' },
]

const STATS = [
  { value: '1,206', label: 'University pages indexed', icon: Globe },
  { value: '15,000+', label: 'Knowledge chunks', icon: Layers },
  { value: '1,536', label: 'Vector dimensions', icon: Network },
  { value: '3', label: 'AI agents in pipeline', icon: Workflow },
]

/** Student-facing chat widget capabilities — marketed on the main page */
const CHAT_FEATURES = [
  {
    icon: MessageCircle,
    title: 'Natural conversation',
    headline: 'Ask in plain English',
    desc: 'Prospective students ask about courses, fees, visas, accommodation, and applications — the assistant replies in clear, friendly language.',
    highlight: 'Session memory keeps context across turns',
  },
  {
    icon: BookOpen,
    title: 'Answers grounded in Stirling',
    headline: 'RAG-backed responses',
    desc: 'Every answer is built from real University of Stirling web content — not generic AI guesses.',
    highlight: 'Shows related stir.ac.uk pages with each reply',
  },
  {
    icon: ListChecks,
    title: 'One-tap starters',
    headline: 'Quick topic chips',
    desc: 'Welcome screen offers instant prompts: next intake, entry requirements, scholarships, how to apply, and campus life.',
    highlight: 'Suggested follow-up questions after each answer',
  },
  {
    icon: Link2,
    title: 'Trust & transparency',
    headline: 'Clickable sources',
    desc: 'Responses link to official pages so users can verify information and explore further on the real university site.',
    highlight: 'Formatted links, emails, and phone numbers',
  },
  {
    icon: Shield,
    title: 'Safe & on-topic',
    headline: 'Built-in guardrails',
    desc: 'Topic boundaries and safety filters keep the assistant focused on university-related questions appropriate for applicants.',
    highlight: 'Prompt-injection detection & rate limiting',
  },
  {
    icon: Maximize2,
    title: 'Flexible UI',
    headline: 'Widget or fullscreen',
    desc: 'Floating chat while browsing the showcase page, or fullscreen for longer sessions. Exit fullscreen to read features below.',
    highlight: 'Fullscreen toggle in the chat header',
  },
]

const ARCHITECTURE_STEPS = [
  { title: 'Router Agent', desc: 'Understands intent and routes the query', icon: Bot, color: 'from-blue-500 to-blue-600' },
  { title: 'RAG Agent', desc: 'Retrieves facts and drafts the answer', icon: Database, color: 'from-emerald-500 to-emerald-600' },
  { title: 'Lead Agent', desc: 'Optional progressive contact capture', icon: Users, color: 'from-purple-500 to-purple-600' },
]

const TECH_STACK = [
  {
    category: 'AI & ML',
    icon: Brain,
    items: [
      { name: 'Claude Sonnet 4', desc: 'Conversational responses' },
      { name: 'OpenAI Embeddings', desc: 'Semantic search (1,536D)' },
      { name: 'LangGraph', desc: 'Multi-agent orchestration' },
    ]
  },
  {
    category: 'Search & RAG',
    icon: Search,
    items: [
      { name: 'Hybrid RAG', desc: 'Vectors + keyword (BM25)' },
      { name: 'Re-ranking', desc: 'Relevance scoring' },
      { name: 'pgvector', desc: 'Postgres vector search' },
    ]
  },
  {
    category: 'Safety',
    icon: Shield,
    items: [
      { name: 'Topic boundaries', desc: 'University scope only' },
      { name: 'Injection guard', desc: 'Input filtering' },
      { name: 'Monitoring', desc: 'Incidents & rate limits' },
    ]
  },
  {
    category: 'Backend',
    icon: Server,
    items: [
      { name: 'FastAPI', desc: 'REST API' },
      { name: 'PostgreSQL', desc: '13 tables' },
      { name: '7 endpoints', desc: 'Chat, feedback, health' },
    ]
  },
  {
    category: 'Frontend',
    icon: Layout,
    items: [
      { name: 'React 18', desc: 'Chat widget UI' },
      { name: 'TailwindCSS', desc: 'Responsive layout' },
      { name: 'Vite', desc: 'Fast builds' },
    ]
  },
  {
    category: 'Data',
    icon: GitBranch,
    items: [
      { name: 'FireCrawl', desc: 'Site scraping' },
      { name: 'Chunking', desc: 'Semantic segments' },
      { name: 'Lead capture', desc: 'Progressive forms' },
    ]
  },
]

const scrollSection = 'scroll-mt-24'

export default function StirlingHomepage() {
  const openChat = () => window.dispatchEvent(new CustomEvent('openChatWidget'))

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-100" style={{ fontFamily: "'Inter', 'Open Sans', system-ui, sans-serif" }}>

      <nav className="sticky top-[42px] sm:top-[44px] z-40 bg-white/90 backdrop-blur-md border-b border-slate-200/60">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex items-center justify-between gap-4">
            <a href="https://www.stir.ac.uk/" className="flex items-center gap-2 sm:gap-3 group shrink-0">
              <img src={IMAGES.logo} alt="University of Stirling" className="h-9 sm:h-11 transition-transform group-hover:scale-105" />
              <span className="text-slate-600 text-xs sm:text-sm font-medium hidden xs:block">Research showcase</span>
            </a>

            <div className="hidden md:flex items-center gap-6">
              {NAV_LINKS.map((link) => (
                <a
                  key={link.href}
                  href={link.href}
                  className="text-sm font-medium text-slate-600 hover:text-emerald-700 transition-colors"
                >
                  {link.label}
                </a>
              ))}
              <button
                type="button"
                onClick={openChat}
                className="text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 px-4 py-2 rounded-lg transition-colors"
              >
                Open chat
              </button>
            </div>

            <div className="flex items-center gap-2 sm:gap-3 shrink-0">
              <span className="text-slate-500 text-xs hidden lg:block">Baqar Jafri</span>
              <div className="h-8 w-8 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-700 flex items-center justify-center text-white text-xs font-bold">
                BJ
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 opacity-30 pointer-events-none">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl" />
        </div>

        <div className={`relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-10 ${scrollSection}`}>
          <div className="flex justify-center mb-6">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-50 border border-emerald-200/80">
              <Sparkles className="w-4 h-4 text-emerald-600" />
              <span className="text-sm font-medium text-emerald-800">MSc research · AI admissions assistant</span>
            </div>
          </div>

          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-bold text-center text-slate-900 mb-5 leading-tight">
            Stirling University
            <span className="block bg-gradient-to-r from-emerald-600 to-blue-600 bg-clip-text text-transparent">
              AI Chat Assistant
            </span>
          </h1>

          <p className="text-base sm:text-xl text-center text-slate-600 max-w-3xl mx-auto mb-8 leading-relaxed">
            A production-style chat widget for prospective students — powered by hybrid RAG over official university content,
            multi-agent orchestration, and safety guardrails. <strong className="text-slate-800">Scroll down</strong> to explore features, then try the chat (bottom-right).
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-12">
            <button
              type="button"
              onClick={openChat}
              className="group inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/25 hover:scale-105 transition-all"
            >
              <MessageSquare className="w-5 h-5" />
              Try the live chat
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
            <a
              href="#chat-features"
              className="inline-flex items-center gap-2 px-6 py-4 text-emerald-800 font-semibold rounded-xl border-2 border-emerald-200 hover:bg-emerald-50 transition-colors"
            >
              See what it can do
              <ChevronRight className="w-5 h-5" />
            </a>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-5">
            {STATS.map((stat, idx) => (
              <div key={idx} className="bg-white/80 backdrop-blur-sm rounded-xl p-4 border border-slate-200/80 text-center sm:text-left">
                <div className="flex flex-col sm:flex-row items-center sm:items-center gap-2 mb-1">
                  <stat.icon className="w-5 h-5 text-emerald-600 shrink-0" />
                  <span className="text-xl sm:text-2xl font-bold text-slate-900">{stat.value}</span>
                </div>
                <p className="text-xs sm:text-sm text-slate-600">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRIMARY: Chat widget features — marketed for visitors */}
      <section id="chat-features" className={`py-16 sm:py-20 bg-white border-y border-slate-100 ${scrollSection}`}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12 max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 mb-3 px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-sm font-semibold">
              <GraduationCap className="w-4 h-4" />
              What the chatbot does for students
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">
              Six features built into the chat experience
            </h2>
            <p className="text-lg text-slate-600">
              This showcase page explains the system; the <strong>chat widget</strong> is the product.
              Use the floating widget while you scroll, or fullscreen when you want a larger view.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {CHAT_FEATURES.map((feature, idx) => (
              <article
                key={idx}
                className="relative flex flex-col p-6 rounded-2xl bg-gradient-to-b from-slate-50 to-white border border-slate-200 hover:border-emerald-400/60 hover:shadow-lg hover:shadow-emerald-500/10 transition-all duration-300"
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center text-white mb-4 shadow-md">
                  <feature.icon className="w-6 h-6" />
                </div>
                <p className="text-xs font-bold uppercase tracking-wider text-emerald-600 mb-1">{feature.title}</p>
                <h3 className="text-xl font-bold text-slate-900 mb-2">{feature.headline}</h3>
                <p className="text-sm text-slate-600 leading-relaxed flex-1 mb-4">{feature.desc}</p>
                <p className="text-xs font-medium text-slate-500 bg-slate-100/80 rounded-lg px-3 py-2 border border-slate-200/80">
                  ✓ {feature.highlight}
                </p>
              </article>
            ))}
          </div>

          <div className="mt-12 text-center">
            <button
              type="button"
              onClick={openChat}
              className="inline-flex items-center gap-2 px-6 py-3 bg-slate-900 text-white font-semibold rounded-xl hover:bg-slate-800 transition-colors"
            >
              <MessageSquare className="w-5 h-5" />
              Open chat and try a quick topic
            </button>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className={`py-16 bg-slate-50 ${scrollSection}`}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 mb-3">
              <Workflow className="w-5 h-5 text-emerald-600" />
              <span className="text-sm font-semibold text-emerald-600 uppercase tracking-wide">How it works</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-3">
              Three agents, one smooth conversation
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Behind each message, a LangGraph pipeline classifies intent, retrieves university content, and optionally captures leads.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 relative">
            <div className="hidden md:block absolute top-1/2 left-[16%] right-[16%] h-0.5 bg-gradient-to-r from-blue-200 via-emerald-200 to-purple-200 -translate-y-1/2" />
            {ARCHITECTURE_STEPS.map((step, idx) => (
              <div key={idx} className="relative z-10 bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${step.color} flex items-center justify-center text-white mb-3`}>
                  <step.icon className="w-6 h-6" />
                </div>
                <span className="text-xs font-bold text-slate-400">Step {idx + 1}</span>
                <h3 className="text-lg font-bold text-slate-900 mt-1 mb-2">{step.title}</h3>
                <p className="text-sm text-slate-600">{step.desc}</p>
              </div>
            ))}
          </div>

          <div className="mt-8 p-4 sm:p-5 bg-white rounded-xl border border-slate-200 overflow-x-auto">
            <div className="flex flex-wrap items-center justify-center gap-2 text-xs sm:text-sm font-medium text-slate-700 min-w-max">
              <span className="px-3 py-1.5 bg-slate-100 rounded-lg">React UI</span>
              <ChevronRight className="w-4 h-4 text-slate-300 shrink-0" />
              <span className="px-3 py-1.5 bg-slate-100 rounded-lg">FastAPI</span>
              <ChevronRight className="w-4 h-4 text-slate-300 shrink-0" />
              <span className="px-3 py-1.5 bg-blue-50 text-blue-800 rounded-lg">Router</span>
              <ChevronRight className="w-4 h-4 text-slate-300 shrink-0" />
              <span className="px-3 py-1.5 bg-emerald-50 text-emerald-800 rounded-lg">RAG</span>
              <ChevronRight className="w-4 h-4 text-slate-300 shrink-0" />
              <span className="px-3 py-1.5 bg-purple-50 text-purple-800 rounded-lg">Lead</span>
              <ChevronRight className="w-4 h-4 text-slate-300 shrink-0" />
              <span className="px-3 py-1.5 bg-slate-800 text-white rounded-lg">PostgreSQL + pgvector</span>
            </div>
          </div>
        </div>
      </section>

      {/* Technology */}
      <section id="technology" className={`py-16 bg-white ${scrollSection}`}>
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 mb-3">
              <Cpu className="w-5 h-5 text-emerald-600" />
              <span className="text-sm font-semibold text-emerald-600 uppercase tracking-wide">Under the hood</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-3">
              Technology stack
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Production-oriented choices for retrieval quality, safety, and deployability.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {TECH_STACK.map((category, idx) => (
              <div key={idx} className="bg-slate-50 rounded-xl p-5 border border-slate-200">
                <div className="flex items-center gap-2 mb-4">
                  <category.icon className="w-5 h-5 text-emerald-600" />
                  <h3 className="font-bold text-slate-900">{category.category}</h3>
                </div>
                <ul className="space-y-3">
                  {category.items.map((item, itemIdx) => (
                    <li key={itemIdx} className="border-l-2 border-emerald-300 pl-3">
                      <p className="font-semibold text-slate-800 text-sm">{item.name}</p>
                      <p className="text-xs text-slate-500">{item.desc}</p>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Research highlights */}
      <section className="py-14 bg-gradient-to-br from-slate-900 to-slate-800 text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <div className="grid sm:grid-cols-2 gap-6 text-left mb-8">
            {[
              { icon: Database, title: 'Hybrid RAG', desc: 'Vector + keyword search with re-ranking for accurate retrieval.' },
              { icon: Shield, title: 'Safety layers', desc: 'Guardrails, topic scope, and monitoring for research-grade control.' },
              { icon: Users, title: 'Lead capture', desc: 'Progressive contact collection integrated into the conversation flow.' },
              { icon: BarChart, title: 'Optional feedback', desc: 'Ratings only when users explicitly end a conversation — never on every close.' },
            ].map((item, i) => (
              <div key={i} className="flex gap-3 p-4 rounded-xl bg-white/5 border border-white/10">
                <item.icon className="w-8 h-8 text-emerald-400 shrink-0" />
                <div>
                  <h3 className="font-bold mb-1">{item.title}</h3>
                  <p className="text-sm text-slate-300">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
          <a
            href="https://www.linkedin.com/in/thebaqarjafri/"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
          >
            <Linkedin className="w-5 h-5" />
            Connect on LinkedIn
          </a>
        </div>
      </section>

      {/* CTA */}
      <section className="py-14 bg-gradient-to-r from-emerald-600 to-emerald-700">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h2 className="text-2xl sm:text-3xl font-bold text-white mb-3">Ready to try it?</h2>
          <p className="text-emerald-100 mb-6">
            Ask about entry requirements, scholarships, or campus life. Exit fullscreen from the chat header to return here anytime.
          </p>
          <button
            type="button"
            onClick={openChat}
            className="inline-flex items-center gap-2 px-8 py-4 bg-white text-emerald-800 font-bold rounded-xl shadow-xl hover:scale-105 transition-all"
          >
            <MessageSquare className="w-6 h-6" />
            Start chatting
          </button>
        </div>
      </section>

      <footer className="bg-slate-900 text-slate-400 py-8">
        <div className="max-w-6xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <img src={IMAGES.logo} alt="" className="h-8 opacity-60" />
            <span className="text-sm">Independent research project · Not affiliated with the University of Stirling</span>
          </div>
          <p className="text-sm">React · FastAPI · LangGraph · Claude</p>
        </div>
      </footer>
    </div>
  )
}

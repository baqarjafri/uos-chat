import { Search, Menu, ChevronRight, Facebook, Instagram, Youtube, Linkedin, GraduationCap } from 'lucide-react'

// Local images - stored in public/images folder
const IMAGES = {
  logo: '/images/stirling-logo.svg',
  hero: '/images/hero-campus.jpg',
  undergraduate: '/images/undergraduate.jpg',
  postgraduate: '/images/postgraduate.jpg',
  research: '/images/research.jpg',
  strategic: '/images/strategic.jpg',
  sport: '/images/sport.jpg',
};

export default function StirlingHomepage() {
  return (
    <div className="min-h-screen bg-white" style={{ fontFamily: "'Open Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif" }}>
      {/* Top Utility Bar */}
      <div className="bg-[#f5f5f5] border-b border-gray-200">
        <div className="max-w-[1400px] mx-auto px-4 py-2">
          <div className="flex justify-between items-center text-[13px]">
            <div className="flex space-x-6">
              <a href="https://www.stir.ac.uk/internal-staff/" className="text-[#333] hover:text-[#006938] transition">Staff</a>
              <a href="https://www.stir.ac.uk/internal-students/" className="text-[#333] hover:text-[#006938] transition">Students</a>
              <a href="https://www.stir.ac.uk/about/our-people/alumni/" className="text-[#333] hover:text-[#006938] transition">Alumni</a>
            </div>
            <div className="flex items-center space-x-4">
              <a href="https://portal.stir.ac.uk/student/enquiry/ask.jsp" className="text-[#333] hover:text-[#006938] transition">Contact</a>
              <button className="text-[#333] hover:text-[#006938] p-1">
                <Search className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Header */}
      <header className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-[1400px] mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <a href="https://www.stir.ac.uk/" className="flex items-center">
              <img 
                src={IMAGES.logo}
                alt="University of Stirling" 
                className="h-[45px] md:h-[55px]"
              />
            </a>
            
            <nav className="hidden lg:flex items-center space-x-1">
              <a href="https://www.stir.ac.uk/study/" className="text-[#333] hover:text-[#006938] transition px-4 py-2 text-[15px] font-medium">Study</a>
              <a href="https://www.stir.ac.uk/research/" className="text-[#333] hover:text-[#006938] transition px-4 py-2 text-[15px] font-medium">Research</a>
              <a href="https://www.stir.ac.uk/about/" className="text-[#333] hover:text-[#006938] transition px-4 py-2 text-[15px] font-medium">About</a>
              <a href="https://www.stir.ac.uk/study/international-students/" className="text-[#333] hover:text-[#006938] transition px-4 py-2 text-[15px] font-medium">International</a>
              <a href="https://www.stir.ac.uk/about/faculties/stirling-management-school/business-engagement/" className="text-[#333] hover:text-[#006938] transition px-4 py-2 text-[15px] font-medium">Business</a>
              <a href="https://www.stir.ac.uk/study/apply/" className="bg-[#006938] text-white px-6 py-2.5 rounded hover:bg-[#005530] transition font-semibold text-[15px] ml-4">
                Apply
              </a>
            </nav>
            
            <button className="lg:hidden p-2">
              <Menu className="w-6 h-6 text-[#333]" />
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative h-[500px] md:h-[600px] bg-cover bg-center" style={{
        backgroundImage: `linear-gradient(rgba(0, 32, 91, 0.6), rgba(0, 32, 91, 0.6)), url("${IMAGES.hero}")`,
        backgroundPosition: 'center center',
        backgroundSize: 'cover'
      }}>
        <div className="max-w-[1400px] mx-auto px-4 h-full flex items-center">
          <div className="max-w-2xl text-white">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 leading-tight">
              Study in Scotland, UK
            </h1>
            <p className="text-lg md:text-xl mb-8 leading-relaxed opacity-95">
              The University of Stirling is a world-class institution with one of the best student experiences in the UK. Are you Stirling?
            </p>
            <div className="flex flex-wrap gap-4">
              <a href="https://www.stir.ac.uk/study/" className="bg-[#006938] text-white px-8 py-3 rounded hover:bg-[#005530] transition font-semibold text-base inline-block">
                Explore courses
              </a>
              <a href="https://www.stir.ac.uk/study/visit-us/" className="border-2 border-white text-white px-8 py-3 rounded hover:bg-white hover:text-[#00205B] transition font-semibold text-base inline-block">
                Visit us
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Study at Stirling - Course Cards */}
      <section className="py-16 md:py-20 bg-white">
        <div className="max-w-[1400px] mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-bold text-[#00205B] mb-10 text-center">
            Study at Stirling - choose your course
          </h2>
          <div className="grid md:grid-cols-3 gap-6 md:gap-8">
            {/* Undergraduate */}
            <a href="https://www.stir.ac.uk/study/undergraduate/" className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-xl transition-shadow group block">
              <div className="h-48 bg-cover bg-center" style={{
                backgroundImage: `url("${IMAGES.undergraduate}")`
              }}></div>
              <div className="p-6">
                <h3 className="text-xl font-bold mb-2 text-[#00205B] group-hover:text-[#006938] transition">Undergraduate</h3>
                <p className="text-gray-600 mb-4 text-[15px]">
                  More than 170 flexible undergraduate degree courses.
                </p>
                <span className="text-[#006938] font-semibold inline-flex items-center text-[15px]">
                  Undergraduate <ChevronRight className="w-4 h-4 ml-1" />
                </span>
              </div>
            </a>

            {/* Postgraduate taught */}
            <a href="https://www.stir.ac.uk/study/postgraduate/" className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-xl transition-shadow group block">
              <div className="h-48 bg-cover bg-center" style={{
                backgroundImage: `url("${IMAGES.postgraduate}")`
              }}></div>
              <div className="p-6">
                <h3 className="text-xl font-bold mb-2 text-[#00205B] group-hover:text-[#006938] transition">Postgraduate taught</h3>
                <p className="text-gray-600 mb-4 text-[15px]">
                  On campus and online Masters courses with multiple start dates.
                </p>
                <span className="text-[#006938] font-semibold inline-flex items-center text-[15px]">
                  Postgraduate taught <ChevronRight className="w-4 h-4 ml-1" />
                </span>
              </div>
            </a>

            {/* Research degrees */}
            <a href="https://www.stir.ac.uk/research/research-degrees/" className="bg-white border border-gray-200 rounded-lg overflow-hidden hover:shadow-xl transition-shadow group block">
              <div className="h-48 bg-cover bg-center" style={{
                backgroundImage: `url("${IMAGES.research}")`
              }}></div>
              <div className="p-6">
                <h3 className="text-xl font-bold mb-2 text-[#00205B] group-hover:text-[#006938] transition">Research degrees</h3>
                <p className="text-gray-600 mb-4 text-[15px]">
                  Find out about our PhD, MPhil and Professional Doctorates.
                </p>
                <span className="text-[#006938] font-semibold inline-flex items-center text-[15px]">
                  Research degrees <ChevronRight className="w-4 h-4 ml-1" />
                </span>
              </div>
            </a>
          </div>
        </div>
      </section>

      {/* Winter Break Notice */}
      <section className="py-12 bg-[#f5f5f5]">
        <div className="max-w-[1400px] mx-auto px-4">
          <div className="bg-white rounded-lg shadow-md p-8 flex flex-col md:flex-row items-center gap-6">
            <div className="flex-1">
              <h2 className="text-2xl md:text-3xl font-bold text-[#00205B] mb-4">
                Campus services and student support over the Winter Break
              </h2>
              <p className="text-gray-600 mb-4 text-[15px] leading-relaxed">
                The University Winter Break runs from 17:00 (GMT) Tuesday 23 December 2025 to 09:00 (GMT) Monday 5 January 2026. Some campus services may be closed or will operate different opening hours.
              </p>
              <a href="https://www.stir.ac.uk/about/christmas-closure-information/" className="text-[#006938] font-semibold inline-flex items-center text-[15px] hover:underline">
                See the availability of University services and their opening hours <ChevronRight className="w-4 h-4 ml-1" />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Cards - Strategic Plan & Sport */}
      <section className="py-16 md:py-20 bg-white">
        <div className="max-w-[1400px] mx-auto px-4">
          <div className="grid md:grid-cols-2 gap-8">
            {/* Strategic Plan 2030 */}
            <a href="https://www.stir.ac.uk/about/strategic-plan/" className="bg-white rounded-lg overflow-hidden shadow-lg hover:shadow-xl transition-shadow group block">
              <div className="h-56 md:h-64 bg-cover bg-center" style={{
                backgroundImage: `url("${IMAGES.strategic}")`
              }}></div>
              <div className="p-8">
                <h3 className="text-2xl md:text-3xl font-bold text-[#00205B] mb-4 group-hover:text-[#006938] transition">
                  Strategic Plan 2030
                </h3>
                <p className="text-gray-600 mb-6 leading-relaxed text-[15px]">
                  Our Strategic Plan sets out the University's direction to 2030. We are confident it will enable us to deliver our ambition to be the difference, to make an impact on people's lives and be a force for good in the world.
                </p>
                <span className="text-[#006938] font-semibold inline-flex items-center text-[15px]">
                  Strategic Plan <ChevronRight className="w-4 h-4 ml-1" />
                </span>
              </div>
            </a>

            {/* Scotland's University for Sporting Excellence */}
            <a href="https://www.stir.ac.uk/student-life/sport-at-stirling/" className="bg-white rounded-lg overflow-hidden shadow-lg hover:shadow-xl transition-shadow group block">
              <div className="h-56 md:h-64 bg-cover bg-center" style={{
                backgroundImage: `url("${IMAGES.sport}")`
              }}></div>
              <div className="p-8">
                <h3 className="text-2xl md:text-3xl font-bold text-[#00205B] mb-4 group-hover:text-[#006938] transition">
                  Scotland's University for Sporting Excellence
                </h3>
                <p className="text-gray-600 mb-6 leading-relaxed text-[15px]">
                  We deliver the best for Scottish sport through the powerful combination of sport and education.
                </p>
                <span className="text-[#006938] font-semibold inline-flex items-center text-[15px]">
                  Sport at Stirling <ChevronRight className="w-4 h-4 ml-1" />
                </span>
              </div>
            </a>
          </div>
        </div>
      </section>

      {/* Research Banner */}
      <section className="py-16 md:py-20 bg-[#00205B] text-white">
        <div className="max-w-[1400px] mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Research
          </h2>
          <p className="text-lg md:text-xl mb-8 max-w-3xl mx-auto leading-relaxed opacity-90">
            Our research makes the difference. Explore our research themes, programmes and spotlight articles to find out how we're impacting the world.
          </p>
          <a href="https://www.stir.ac.uk/research/" className="bg-[#006938] text-white px-8 py-3 rounded hover:bg-[#005530] transition font-semibold text-base inline-block">
            Explore our research
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#1a1a1a] text-white">
        {/* Social Links */}
        <div className="border-b border-gray-700">
          <div className="max-w-[1400px] mx-auto px-4 py-6">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <span className="text-[15px] font-medium">Follow us</span>
              <div className="flex items-center space-x-4">
                <a href="https://www.facebook.com/universityofstirling/" className="text-gray-400 hover:text-white transition p-2" aria-label="Facebook">
                  <Facebook className="w-5 h-5" />
                </a>
                <a href="https://www.instagram.com/universityofstirling/" className="text-gray-400 hover:text-white transition p-2" aria-label="Instagram">
                  <Instagram className="w-5 h-5" />
                </a>
                <a href="https://x.com/StirUni" className="text-gray-400 hover:text-white transition p-2" aria-label="X/Twitter">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
                </a>
                <a href="https://www.youtube.com/user/UniversityOfStirling" className="text-gray-400 hover:text-white transition p-2" aria-label="YouTube">
                  <Youtube className="w-5 h-5" />
                </a>
                <a href="https://www.linkedin.com/school/university-of-stirling/" className="text-gray-400 hover:text-white transition p-2" aria-label="LinkedIn">
                  <Linkedin className="w-5 h-5" />
                </a>
                <a href="https://www.tiktok.com/@universityofstirling/" className="text-gray-400 hover:text-white transition p-2" aria-label="TikTok">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z"/></svg>
                </a>
              </div>
            </div>
          </div>
        </div>

        {/* Popular Links */}
        <div className="border-b border-gray-700">
          <div className="max-w-[1400px] mx-auto px-4 py-8">
            <h4 className="text-[15px] font-semibold mb-4">Popular links</h4>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              <a href="https://www.stir.ac.uk/about/faculties/" className="text-gray-400 hover:text-white text-[14px] transition">Faculties</a>
              <a href="https://www.stir.ac.uk/about/professional-services/" className="text-gray-400 hover:text-white text-[14px] transition">Professional services</a>
              <a href="https://www.stir.ac.uk/about/our-people/alumni/" className="text-gray-400 hover:text-white text-[14px] transition">Alumni</a>
              <a href="https://www.stir.ac.uk/about/work-at-stirling/" className="text-gray-400 hover:text-white text-[14px] transition">Jobs at Stirling</a>
              <a href="https://www.stir.ac.uk/about/getting-here/" className="text-gray-400 hover:text-white text-[14px] transition">Getting here</a>
              <a href="https://www.stir.ac.uk/student-life/students-union/" className="text-gray-400 hover:text-white text-[14px] transition">Students' Union</a>
              <a href="https://shop.stir.ac.uk/" className="text-gray-400 hover:text-white text-[14px] transition">Online shop</a>
              <a href="https://blog.stir.ac.uk/" className="text-gray-400 hover:text-white text-[14px] transition">Blog</a>
              <a href="https://www.stir.ac.uk/internal-students/" className="text-gray-400 hover:text-white text-[14px] transition">Current students</a>
              <a href="https://www.stir.ac.uk/internal-staff/" className="text-gray-400 hover:text-white text-[14px] transition">Staff</a>
            </div>
          </div>
        </div>

        {/* Site Information */}
        <div className="border-b border-gray-700">
          <div className="max-w-[1400px] mx-auto px-4 py-6">
            <h4 className="text-[15px] font-semibold mb-4">Site information</h4>
            <div className="flex flex-wrap gap-4 md:gap-6">
              <a href="https://www.stir.ac.uk/about/policy-legal-and-cookies/" className="text-gray-400 hover:text-white text-[14px] transition">Policy, Legal and Cookies</a>
              <a href="https://www.stir.ac.uk/about/accessibility/" className="text-gray-400 hover:text-white text-[14px] transition">Accessibility statement</a>
              <a href="https://www.stir.ac.uk/sitemap/" className="text-gray-400 hover:text-white text-[14px] transition">Sitemap</a>
              <a href="https://www.stir.ac.uk/about/modern-slavery-statement/" className="text-gray-400 hover:text-white text-[14px] transition">Modern Slavery Statement</a>
              <a href="https://www.stir.ac.uk/about/" className="text-gray-400 hover:text-white text-[14px] transition">Scottish Charity No SC011159</a>
            </div>
          </div>
        </div>

        {/* Contact & Copyright */}
        <div className="max-w-[1400px] mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex flex-col md:flex-row items-center gap-4 text-[14px]">
              <span className="font-semibold">Contact us</span>
              <a href="tel:+441786473171" className="text-gray-400 hover:text-white transition">Tel: +44 (0) 1786 473171</a>
              <a href="https://portal.stir.ac.uk/student/enquiry/ask.jsp" className="text-[#006938] hover:text-[#00a050] transition font-medium">Ask us a question ›</a>
            </div>
            <p className="text-gray-400 text-[14px]">© University of Stirling</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

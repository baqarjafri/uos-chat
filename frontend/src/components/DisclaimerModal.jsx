import { useState, useEffect } from 'react';
import { AlertTriangle, X } from 'lucide-react';

export default function DisclaimerModal() {
  const [isVisible, setIsVisible] = useState(false);
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    const hasAccepted = localStorage.getItem('stirling_disclaimer_accepted');
    if (!hasAccepted) {
      setIsVisible(true);
    }
  }, []);

  const handleAccept = () => {
    setIsClosing(true);
    setTimeout(() => {
      localStorage.setItem('stirling_disclaimer_accepted', 'true');
      localStorage.setItem('stirling_disclaimer_accepted_date', new Date().toISOString());
      setIsVisible(false);
      setIsClosing(false);
    }, 300);
  };

  if (!isVisible) return null;

  return (
    <div 
      className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black transition-opacity duration-300 ${
        isClosing ? 'bg-opacity-0' : 'bg-opacity-60'
      }`}
      style={{ backdropFilter: 'blur(4px)' }}
    >
      <div 
        className={`bg-white rounded-lg shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto transform transition-all duration-300 ${
          isClosing ? 'scale-95 opacity-0' : 'scale-100 opacity-100'
        }`}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-[#00205B] to-[#003d82] text-white p-6 rounded-t-lg">
          <div className="flex items-start gap-4">
            <div className="flex-shrink-0 mt-1">
              <AlertTriangle className="w-8 h-8 text-yellow-300" />
            </div>
            <div className="flex-1">
              <h2 className="text-2xl font-bold mb-2">
                ACADEMIC RESEARCH PROJECT
              </h2>
              <p className="text-lg font-semibold text-yellow-300">
                PROOF OF CONCEPT DISCLAIMER
              </p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Important Notice */}
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
            <p className="text-sm font-bold text-gray-800 mb-2">
              ⚠️ IMPORTANT NOTICE - PLEASE READ CAREFULLY
            </p>
            <p className="text-sm text-gray-700">
              This is an academic research proof-of-concept developed as part of an MSc project at the University of Stirling.
            </p>
          </div>

          {/* Purpose & Scope */}
          <div>
            <h3 className="text-lg font-bold text-[#00205B] mb-3 flex items-center gap-2">
              <span className="text-[#006938]">●</span> PURPOSE & SCOPE
            </h3>
            <ul className="space-y-2 text-sm text-gray-700 ml-4">
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">•</span>
                <span>This is a <strong>PROOF OF CONCEPT</strong> for academic research and evaluation purposes <strong>ONLY</strong></span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">•</span>
                <span>Developed specifically to gather feedback from authorized reviewers</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">•</span>
                <span><strong>NOT</strong> an official University of Stirling service or product</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">•</span>
                <span><strong>NOT</strong> intended for public use or commercial deployment</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">•</span>
                <span><strong>NOT</strong> a production-ready system</span>
              </li>
            </ul>
          </div>

          {/* Authorized Access */}
          <div>
            <h3 className="text-lg font-bold text-[#00205B] mb-3 flex items-center gap-2">
              <span className="text-[#006938]">●</span> AUTHORIZED ACCESS
            </h3>
            <p className="text-sm text-gray-700 mb-3">
              This system is intended <strong>EXCLUSIVELY</strong> for:
            </p>
            <ul className="space-y-2 text-sm text-gray-700 ml-4">
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">•</span>
                <span>University of Stirling employees and staff members</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">•</span>
                <span>Individuals who have been explicitly sent access credentials/links by the project owner (baj00042@students.stir.ac.uk)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">•</span>
                <span>Academic evaluators and supervisors involved in this MSc project</span>
              </li>
            </ul>
            <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
              <p className="text-sm text-red-800 font-semibold">
                If you have NOT received explicit authorization from the project owner, you should NOT proceed.
              </p>
            </div>
          </div>

          {/* Data & Privacy Notice */}
          <div>
            <h3 className="text-lg font-bold text-[#00205B] mb-3 flex items-center gap-2">
              <span className="text-[#006938]">●</span> DATA & PRIVACY NOTICE
            </h3>
            <ul className="space-y-2 text-sm text-gray-700 ml-4">
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">•</span>
                <span>All interactions, conversations, and usage data will be logged and recorded</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">•</span>
                <span>Data collected is for academic evaluation and research purposes only</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-600 mt-1">•</span>
                <span className="font-semibold text-red-700">DO NOT enter any personal, sensitive, or confidential information</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-red-600 mt-1">•</span>
                <span className="font-semibold text-red-700">DO NOT use this system for any real university business or inquiries</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">•</span>
                <span>This system is provided "AS-IS" without any warranties or guarantees</span>
              </li>
            </ul>
          </div>

          {/* Consent & Acknowledgment */}
          <div>
            <h3 className="text-lg font-bold text-[#00205B] mb-3 flex items-center gap-2">
              <span className="text-[#006938]">●</span> CONSENT & ACKNOWLEDGMENT
            </h3>
            <p className="text-sm text-gray-700 mb-3">
              By clicking <strong>"Accept and Continue"</strong> below, you explicitly acknowledge and agree that:
            </p>
            <ul className="space-y-2 text-sm text-gray-700 ml-4">
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">✓</span>
                <span>You understand this is a proof-of-concept research prototype</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">✓</span>
                <span>You are an authorized reviewer (university staff/employee or explicitly invited by the project owner)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">✓</span>
                <span>You consent to all interactions being recorded for academic evaluation purposes</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">✓</span>
                <span>You will provide feedback to support this academic research</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">✓</span>
                <span>You will NOT share any sensitive, personal, or confidential information</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">✓</span>
                <span>You understand this is NOT an official university service</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-[#006938] mt-1">✓</span>
                <span>You will use this system solely for review and feedback purposes</span>
              </li>
            </ul>
          </div>

          {/* Contact Information */}
          <div className="bg-blue-50 border border-blue-200 rounded p-4">
            <h3 className="text-sm font-bold text-[#00205B] mb-2">
              CONTACT INFORMATION
            </h3>
            <p className="text-sm text-gray-700 mb-2">
              For questions, concerns, or feedback about this project:
            </p>
            <p className="text-sm text-gray-700">
              <strong>Email:</strong> <a href="mailto:baj00042@students.stir.ac.uk" className="text-[#006938] hover:underline font-semibold">baj00042@students.stir.ac.uk</a>
            </p>
            <p className="text-sm text-gray-700">
              <strong>Project Owner:</strong> Baqar Jafri, MSc Student, University of Stirling
            </p>
          </div>

          {/* Exit Notice */}
          <div className="text-center p-3 bg-gray-50 rounded">
            <p className="text-xs text-gray-600 italic">
              If you do not agree with these terms or are not an authorized reviewer, please close this window immediately.
            </p>
          </div>
        </div>

        {/* Footer with Accept Button */}
        <div className="bg-gray-50 px-6 py-4 rounded-b-lg border-t border-gray-200">
          <button
            onClick={handleAccept}
            className="w-full bg-[#006938] text-white px-6 py-4 rounded-lg hover:bg-[#005530] transition-colors font-bold text-base shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98] transition-all duration-200"
          >
            I Accept and Agree - Continue to Site
          </button>
          <p className="text-xs text-gray-500 text-center mt-3">
            This disclaimer will only appear once. Your acceptance will be stored locally in your browser.
          </p>
        </div>
      </div>
    </div>
  );
}

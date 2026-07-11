import React, { useState } from 'react';
import { ChevronDown, Check, X, Search, Plus, ArrowRight, Trash2, Globe, MapPin, Laptop, Shield, Target } from 'lucide-react';

export interface TargetCountryConfig {
  country: string;
  remote_only: boolean;
  requires_visa: boolean;
  min_match_score: number;
  active: boolean;
}

interface Step1ProfileProps {
  language: 'ar' | 'en';
  t: any;
  selectedJobTitles: string[];
  setSelectedJobTitles: (titles: string[]) => void;
  targetCountries: TargetCountryConfig[];
  setTargetCountries: (countries: TargetCountryConfig[]) => void;
  yearsOfExperience: string;
  setYearsOfExperience: (exp: string) => void;
  excludeKeywords: string;
  setExcludeKeywords: (kw: string) => void;
  scanFrequency: string;
  setScanFrequency: (freq: string) => void;
  onNext: () => void;
}

const COMMON_JOB_TITLES = [
  'React Developer',
  'Frontend Engineer',
  'Backend Engineer',
  'Fullstack Developer',
  'UI/UX Designer',
  'Product Manager',
  'Mobile App Developer',
  'iOS Developer',
  'Android Developer',
  'Flutter Developer',
  'React Native Developer',
  'Game Developer',
  'Embedded Systems Engineer',
  'DevOps Engineer',
  'Cloud Architect',
  'Cybersecurity Engineer',
  'QA Engineer',
  'Test Automation Engineer',
  'Data Scientist',
  'Machine Learning Engineer',
  'Data Analyst',
  'Data Engineer',
  'AI Research Scientist',
  'Product Designer',
  'Graphic Designer',
  'Motion Designer',
  '3D Artist',
  'Project Manager',
  'Scrum Master',
  'Business Analyst',
  'Digital Marketing Specialist',
  'Content Writer / Copywriter',
  'SEO Specialist',
  'Social Media Manager',
  'Growth Hacker',
  'Business Development Representative (BDR)',
  'Sales Manager',
  'Customer Success Manager',
  'Technical Support Specialist',
  'HR Manager / Recruiter',
  'Operations Manager',
  'Financial Analyst',
];

const COUNTRIES_LIST = {
  ar: [
    { id: 'Worldwide', name: 'عالمي / ريموت', code: 'WW' },
    { id: 'Egypt', name: 'مصر', code: 'EG' },
    { id: 'Saudi Arabia', name: 'السعودية', code: 'SA' },
    { id: 'United Arab Emirates', name: 'الإمارات', code: 'AE' },
    { id: 'Qatar', name: 'قطر', code: 'QA' },
    { id: 'Kuwait', name: 'الكويت', code: 'KW' },
    { id: 'Oman', name: 'عُمان', code: 'OM' },
    { id: 'Bahrain', name: 'البحرين', code: 'BH' },
    { id: 'Jordan', name: 'الأردن', code: 'JO' },
    { id: 'Germany', name: 'ألمانيا', code: 'DE' },
    { id: 'United Kingdom', name: 'المملكة المتحدة', code: 'GB' },
    { id: 'United States', name: 'الولايات المتحدة', code: 'US' },
    { id: 'Canada', name: 'كندا', code: 'CA' },
    { id: 'Netherlands', name: 'هولندا', code: 'NL' },
    { id: 'France', name: 'فرنسا', code: 'FR' },
    { id: 'Sweden', name: 'السويد', code: 'SE' },
    { id: 'Switzerland', name: 'سويسرا', code: 'CH' },
    { id: 'Australia', name: 'أستراليا', code: 'AU' },
  ],
  en: [
    { id: 'Worldwide', name: 'Worldwide / Remote', code: 'WW' },
    { id: 'Egypt', name: 'Egypt', code: 'EG' },
    { id: 'Saudi Arabia', name: 'Saudi Arabia', code: 'SA' },
    { id: 'United Arab Emirates', name: 'United Arab Emirates', code: 'AE' },
    { id: 'Qatar', name: 'Qatar', code: 'QA' },
    { id: 'Kuwait', name: 'Kuwait', code: 'KW' },
    { id: 'Oman', name: 'Oman', code: 'OM' },
    { id: 'Bahrain', name: 'Bahrain', code: 'BH' },
    { id: 'Jordan', name: 'Jordan', code: 'JO' },
    { id: 'Germany', name: 'Germany', code: 'DE' },
    { id: 'United Kingdom', name: 'United Kingdom', code: 'GB' },
    { id: 'United States', name: 'United States', code: 'US' },
    { id: 'Canada', name: 'Canada', code: 'CA' },
    { id: 'Netherlands', name: 'Netherlands', code: 'NL' },
    { id: 'France', name: 'France', code: 'FR' },
    { id: 'Sweden', name: 'Sweden', code: 'SE' },
    { id: 'Switzerland', name: 'Switzerland', code: 'CH' },
    { id: 'Australia', name: 'Australia', code: 'AU' },
  ]
};

export default function Step1Profile({
  language,
  t,
  selectedJobTitles,
  setSelectedJobTitles,
  targetCountries,
  setTargetCountries,
  yearsOfExperience,
  setYearsOfExperience,
  excludeKeywords,
  setExcludeKeywords,
  scanFrequency,
  setScanFrequency,
  onNext
}: Step1ProfileProps) {
  // Dropdown States
  const [jobDropdownOpen, setJobDropdownOpen] = useState(false);
  const [jobSearch, setJobSearch] = useState('');
  const [countryDropdownOpen, setCountryDropdownOpen] = useState(false);
  const [countrySearch, setCountrySearch] = useState('');

  // Filters
  const filteredJobTitles = COMMON_JOB_TITLES.filter(title => 
    title.toLowerCase().includes(jobSearch.toLowerCase()) && !selectedJobTitles.includes(title)
  );

  const countries = COUNTRIES_LIST[language];
  const filteredCountries = countries.filter(c => 
    c.name.toLowerCase().includes(countrySearch.toLowerCase()) || 
    c.id.toLowerCase().includes(countrySearch.toLowerCase())
  );

  const handleAddCountry = (id: string) => {
    if (targetCountries.some(tc => tc.country === id)) {
      // If already added, remove it (toggle behavior)
      setTargetCountries(targetCountries.filter(tc => tc.country !== id));
    } else {
      const newConfig: TargetCountryConfig = {
        country: id,
        remote_only: id === 'Worldwide',
        requires_visa: id !== 'Worldwide' && id !== 'Egypt',
        min_match_score: 65,
        active: true
      };
      setTargetCountries([...targetCountries, newConfig]);
    }
  };

  const handleUpdateCountryRule = (id: string, updates: Partial<TargetCountryConfig>) => {
    setTargetCountries(targetCountries.map(tc => {
      if (tc.country === id) {
        return { ...tc, ...updates };
      }
      return tc;
    }));
  };

  const handleAddCustomJob = () => {
    const trimmed = jobSearch.trim();
    if (trimmed && !selectedJobTitles.includes(trimmed)) {
      setSelectedJobTitles([...selectedJobTitles, trimmed]);
      setJobSearch('');
    }
  };

  const hasSelection = selectedJobTitles.length > 0 && targetCountries.length > 0;

  return (
    <div className="space-y-6">
      
      {/* ─── SECTION 1: GLOBAL JOB CONFIGURATION ─── */}
      <div className="p-4 rounded-xl border border-white/[0.05] bg-white/[0.01] space-y-4">
        <h3 className="text-sm font-bold text-blue-400 uppercase tracking-wider flex items-center gap-1.5 font-sans">
          <Globe className="h-4 w-4" />
          {language === 'ar' ? 'إعدادات البحث العامة' : 'Global Search Settings'}
        </h3>

        {/* Job Titles Search & Multi-Select */}
        <div className="relative font-sans z-30">
          <label className="block text-slate-300 text-xs font-bold mb-2">{t.jobTitlesLabel}</label>
          <div className="flex flex-wrap gap-1.5 p-2 rounded-md border border-white/[0.08] bg-[#030712] min-h-[40px] items-center">
            {selectedJobTitles.map(title => (
              <span key={title} className="inline-flex items-center gap-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 text-xs px-2.5 py-1 rounded">
                {title}
                <button type="button" onClick={() => setSelectedJobTitles(selectedJobTitles.filter(t => t !== title))}>
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
            <button
              type="button"
              onClick={() => {
                setJobDropdownOpen(!jobDropdownOpen);
                setCountryDropdownOpen(false);
              }}
              className="text-slate-500 hover:text-white text-xs px-2 font-medium flex items-center gap-1 ms-auto"
            >
              <ChevronDown className="h-3 w-3" />
            </button>
          </div>

          {jobDropdownOpen && (
            <div className="absolute z-35 mt-1 w-full rounded-md border border-white/[0.08] bg-[#050b18] shadow-lg p-2 space-y-2">
              <div className="relative">
                <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
                <input
                  type="text"
                  placeholder={t.jobSearchPlaceholder}
                  value={jobSearch}
                  onChange={(e) => setJobSearch(e.target.value)}
                  className="w-full h-8 pr-9 pl-3 rounded bg-[#030712] border border-white/[0.08] text-xs text-slate-200 focus:ring-1 focus:ring-blue-500 outline-none"
                />
              </div>
              <div className="max-h-36 overflow-y-auto space-y-0.5 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-white/[0.02] [&::-webkit-scrollbar-thumb]:bg-white/10 [&::-webkit-scrollbar-thumb]:rounded-full font-mono">
                {filteredJobTitles.map(title => (
                  <button
                    key={title}
                    type="button"
                    onClick={() => {
                      setSelectedJobTitles([...selectedJobTitles, title]);
                      setJobSearch('');
                    }}
                    className="w-full h-8 px-3 rounded text-right text-xs text-slate-300 hover:bg-white/[0.04] block font-sans"
                  >
                    {title}
                  </button>
                ))}
                {jobSearch.trim() && !COMMON_JOB_TITLES.includes(jobSearch.trim()) && (
                  <button
                    type="button"
                    onClick={handleAddCustomJob}
                    className="w-full h-8 px-3 rounded text-right text-xs text-blue-400 hover:bg-white/[0.04] flex items-center justify-between font-sans"
                  >
                    <span>{t.customJobBtn} "{jobSearch.trim()}"</span>
                    <Plus className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Side-by-side Row: Years of Experience & Scan Frequency */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 font-sans">
          
          {/* Target Years of Experience */}
          <div>
            <label className="block text-slate-300 text-xs font-bold mb-2">{t.experienceLabel}</label>
            <div className="relative inline-flex items-center w-full">
              <select
                value={yearsOfExperience}
                onChange={(e) => setYearsOfExperience(e.target.value)}
                className="appearance-none [&::-ms-expand]:hidden w-full h-10 rounded-md border border-white/[0.08] bg-[#030712] ps-4 pe-12 text-sm text-slate-100 focus:ring-1 focus:ring-blue-500 outline-none cursor-pointer text-start"
                dir={language === 'ar' ? 'rtl' : 'ltr'}
              >
                {language === 'ar' ? (
                  <>
                    <option value="0-1" className="bg-[#050b18] text-slate-100">مبتدئ (0-1 سنة)</option>
                    <option value="1-3" className="bg-[#050b18] text-slate-100">جونيور (1-3 سنوات)</option>
                    <option value="3-5" className="bg-[#050b18] text-slate-100">ميد-ليفل (3-5 سنوات)</option>
                    <option value="5-8" className="bg-[#050b18] text-slate-100">سينيور (5-8 سنوات)</option>
                    <option value="8+" className="bg-[#050b18] text-slate-100">ليد / خبير (أكثر من 8 سنوات)</option>
                  </>
                ) : (
                  <>
                    <option value="0-1" className="bg-[#050b18] text-slate-100">Entry-Level (0-1 years)</option>
                    <option value="1-3" className="bg-[#050b18] text-slate-100">Junior (1-3 years)</option>
                    <option value="3-5" className="bg-[#050b18] text-slate-100">Mid-Level (3-5 years)</option>
                    <option value="5-8" className="bg-[#050b18] text-slate-100">Senior (5-8 years)</option>
                    <option value="8+" className="bg-[#050b18] text-slate-100">Lead / Principal (8+ years)</option>
                  </>
                )}
              </select>
              <ChevronDown strokeWidth={2.5} className="absolute top-1/2 -translate-y-1/2 h-4 w-4 text-slate-100 pointer-events-none end-4" />
            </div>
          </div>

          {/* Scan Frequency Selector */}
          <div>
            <label className="block text-slate-300 text-xs font-bold mb-2">
              {language === 'ar' ? 'معدل تكرار البحث التلقائي' : 'Automatic Scan Frequency'}
            </label>
            <div className="relative inline-flex items-center w-full">
              <select
                value={scanFrequency}
                onChange={(e) => setScanFrequency(e.target.value)}
                className="appearance-none [&::-ms-expand]:hidden w-full h-10 rounded-md border border-white/[0.08] bg-[#030712] ps-4 pe-12 text-sm focus:ring-1 focus:ring-blue-500 outline-none text-slate-100 cursor-pointer text-start"
                dir={language === 'ar' ? 'rtl' : 'ltr'}
              >
                <option value="20m" className="bg-[#050b18] text-slate-100">{language === 'ar' ? 'كل 20 دقيقة (مستحسن)' : 'Every 20 min (Recommended)'}</option>
                <option value="1h" className="bg-[#050b18] text-slate-100">{language === 'ar' ? 'كل ساعة' : 'Every 1 hour'}</option>
                <option value="6h" className="bg-[#050b18] text-slate-100">{language === 'ar' ? 'كل 6 ساعات' : 'Every 6 hours'}</option>
                <option value="1d" className="bg-[#050b18] text-slate-100">{language === 'ar' ? 'مرة واحدة يومياً' : 'Once daily'}</option>
              </select>
              <ChevronDown strokeWidth={2.5} className="absolute top-1/2 -translate-y-1/2 h-4 w-4 text-slate-100 pointer-events-none end-4" />
            </div>
          </div>

        </div>

        {/* Exclusion Keywords */}
        <div className="font-sans">
          <label className="block text-slate-300 text-xs font-bold mb-2">
            {language === 'ar' ? 'الكلمات المستبعدة (تفصل بفاصلة)' : 'Exclusion Keywords (comma separated)'}
          </label>
          <input
            type="text"
            value={excludeKeywords}
            onChange={(e) => setExcludeKeywords(e.target.value)}
            placeholder={language === 'ar' ? 'مثال: junior, intern, PHP, Amazon' : 'e.g. junior, intern, PHP, Amazon'}
            className="w-full h-10 px-4 rounded-md border border-white/[0.08] bg-[#030712] text-sm text-slate-100 placeholder-slate-600 focus:ring-1 focus:ring-blue-500 outline-none"
          />
        </div>
      </div>

      {/* ─── SECTION 2: TARGET COUNTRIES & OVERRIDES ─── */}
      <div className="p-4 rounded-xl border border-white/[0.05] bg-white/[0.01] space-y-4">
        <div className="flex items-center justify-between font-sans">
          <h3 className="text-sm font-bold text-orange-400 uppercase tracking-wider flex items-center gap-1.5">
            <MapPin className="h-4 w-4" />
            {language === 'ar' ? 'البلدان وقواعد التصفية' : 'Target Countries & Rules'}
          </h3>
          
          {/* Add Country Trigger Dropdown */}
          <div className="relative z-40">
            <button
              type="button"
              onClick={() => {
                setCountryDropdownOpen(!countryDropdownOpen);
                setJobDropdownOpen(false);
              }}
              className="px-3 h-8 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold flex items-center gap-1.5 transition-all"
            >
              <Plus className="h-3.5 w-3.5" />
              {language === 'ar' ? 'إضافة بلد' : 'Add Country'}
            </button>

            {countryDropdownOpen && (
              <div className="absolute left-0 right-auto md:left-auto md:right-0 z-35 mt-1 w-64 rounded-md border border-white/[0.08] bg-[#050b18] shadow-lg p-2 space-y-2">
                <div className="relative">
                  <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500" />
                  <input
                    type="text"
                    placeholder={t.countrySearchPlaceholder}
                    value={countrySearch}
                    onChange={(e) => setCountrySearch(e.target.value)}
                    className="w-full h-8 pr-9 pl-3 rounded bg-[#030712] border border-white/[0.08] text-xs text-slate-200 focus:ring-1 focus:ring-blue-500 outline-none"
                  />
                </div>
                <div className="max-h-48 overflow-y-auto space-y-0.5 [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-white/[0.02] [&::-webkit-scrollbar-thumb]:bg-white/10 [&::-webkit-scrollbar-thumb]:rounded-full">
                  {filteredCountries.map((country) => {
                    const isAdded = targetCountries.some(tc => tc.country === country.id);
                    return (
                      <button
                        key={country.id}
                        type="button"
                        onClick={() => {
                          handleAddCountry(country.id);
                          setCountryDropdownOpen(false);
                          setCountrySearch('');
                        }}
                        className="w-full h-8 px-3 rounded text-right text-xs text-slate-300 hover:bg-white/[0.04] flex items-center justify-between"
                      >
                        <span className="flex items-center gap-2">
                          <span className="text-[10px] font-mono font-bold bg-white/10 border border-white/10 px-1.5 py-0.5 rounded text-slate-400 select-none uppercase">{country.code}</span>
                          <span>{country.name}</span>
                        </span>
                        {isAdded && <Check className="h-3.5 w-3.5 text-blue-500" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Dynamic List of Active Country Rules Cards */}
        {targetCountries.length === 0 ? (
          <div className="text-center py-8 rounded-lg border border-dashed border-white/[0.08] p-4 text-xs text-slate-500 font-sans">
            {language === 'ar'
              ? 'يرجى إضافة بلد مستهدف واحد على الأقل للبدء بالفحص.'
              : 'Please add at least one target country to start scanning.'}
          </div>
        ) : (
          <div className="space-y-3 font-sans max-h-[280px] overflow-y-auto pr-1.5 pl-0.5 [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-track]:bg-white/[0.01] [&::-webkit-scrollbar-thumb]:bg-white/10 [&::-webkit-scrollbar-thumb]:rounded-full">
            {targetCountries.map((tc) => {
              const countryInfo = countries.find(c => c.id === tc.country);
              return (
                <div 
                  key={tc.country} 
                  className="p-3 rounded-xl border border-white/[0.08] bg-[#050b18]/80 hover:border-white/[0.12] transition-all relative overflow-hidden"
                >
                  {/* Card Header */}
                  <div className="flex items-center justify-between pb-2 border-b border-white/[0.04] mb-2">
                    <div className="flex items-center gap-2 text-sm font-bold text-white">
                      <span className="text-[10px] font-mono font-bold bg-white/10 border border-white/10 px-1.5 py-0.5 rounded text-slate-400 select-none uppercase">{countryInfo?.code || tc.country.substring(0, 2).toUpperCase()}</span>
                      <span>{countryInfo?.name || tc.country}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setTargetCountries(targetCountries.filter(item => item.country !== tc.country))}
                      className="h-7 w-7 rounded-lg hover:bg-red-500/10 text-slate-400 hover:text-red-400 transition-colors flex items-center justify-center"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>

                  {/* Card Controls Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    
                    {/* Toggles */}
                    <div className="space-y-3">
                      {/* Remote Only Toggle */}
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-slate-300 flex items-center gap-1.5">
                          <Laptop className="h-3.5 w-3.5 text-blue-400" />
                          {language === 'ar' ? 'عمل عن بعد فقط' : 'Remote Only'}
                        </span>
                        <label className="relative inline-flex items-center cursor-pointer">
                          <input 
                            type="checkbox" 
                            checked={tc.remote_only} 
                            onChange={(e) => handleUpdateCountryRule(tc.country, { remote_only: e.target.checked })}
                            className="sr-only peer"
                          />
                          <div className="w-9 h-5 bg-white/[0.08] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:right-[2px] peer-checked:after:right-[16px] after:bg-slate-400 peer-checked:after:bg-blue-400 after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-500/25 border border-white/[0.08]" />
                        </label>
                      </div>

                      {/* Requires Visa Toggle (Hidden for Worldwide) */}
                      {tc.country !== 'Worldwide' && (
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-slate-300 flex items-center gap-1.5">
                            <Shield className="h-3.5 w-3.5 text-purple-400" />
                            {language === 'ar' ? 'يتطلب تأشيرة / رعاية' : 'Requires Visa Sponsorship'}
                          </span>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input 
                              type="checkbox" 
                              checked={tc.requires_visa} 
                              disabled={tc.country === 'Egypt'} // local country doesn't require visa
                              onChange={(e) => handleUpdateCountryRule(tc.country, { requires_visa: e.target.checked })}
                              className="sr-only peer"
                            />
                            <div className="w-9 h-5 bg-white/[0.08] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:right-[2px] peer-checked:after:right-[16px] after:bg-slate-400 peer-checked:after:bg-blue-400 after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-blue-500/25 border border-white/[0.08] disabled:opacity-30" />
                          </label>
                        </div>
                      )}
                    </div>

                    {/* AI Score Slider */}
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-slate-300 flex items-center gap-1.5">
                          <Target className="h-3.5 w-3.5 text-orange-400" />
                          {language === 'ar' ? 'الحد الأدنى للقبول (AI)' : 'Min match score (AI)'}
                        </span>
                        <span className="text-xs font-bold text-blue-400">{tc.min_match_score}%</span>
                      </div>
                      <input
                        type="range"
                        min="50"
                        max="95"
                        value={tc.min_match_score}
                        onChange={(e) => handleUpdateCountryRule(tc.country, { min_match_score: parseInt(e.target.value) })}
                        className="w-full h-1.5 rounded-lg bg-white/[0.08] appearance-none cursor-pointer accent-blue-500"
                      />
                    </div>

                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <button
        onClick={onNext}
        disabled={!hasSelection}
        className="w-full h-10 mt-8 rounded-md bg-blue-600 hover:bg-blue-700 hover:scale-[1.02] active:scale-[0.98] transition-all text-white font-semibold text-sm flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 font-sans"
      >
        {t.nextBtn}
        <ArrowRight className={`h-4 w-4 ${language === 'ar' ? 'rotate-180' : ''}`} />
      </button>
    </div>
  );
}

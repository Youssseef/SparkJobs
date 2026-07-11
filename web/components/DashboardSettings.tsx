import React, { useState } from 'react';
import { Settings, Laptop, Shield, Target, Plus, X, Upload, FileText, Check, RotateCw, Globe, Sliders, AlertTriangle } from 'lucide-react';
import { TargetCountryConfig } from './Step1Profile';

interface DashboardSettingsProps {
  config: any;
  setConfig: (config: any) => void;
  repoName: string;
  githubToken: string;
  language: 'ar' | 'en';
  onReSetup: () => void;
  chatId: string;
  cvFileName: string;
  setCvFileName: (name: string) => void;
}

const TRANSLATIONS = {
  ar: {
    title: 'إعدادات البحث والـ CV',
    globalConfigTitle: 'خيارات البحث العامة',
    jobTitles: 'المسميات الوظيفية المستهدفة',
    experience: 'سنوات الخبرة',
    exclusions: 'الكلمات المستبعدة',
    frequency: 'تكرار الفحص',
    countriesTitle: 'قواعد التصفية للبلدان المستهدفة',
    cvTitle: 'السيرة الذاتية (CV)',
    currentCv: 'الملف الحالي:',
    replaceCvBtn: 'تبديل الملف',
    saveSettingsBtn: 'حفظ جميع التعديلات',
    saveSuccess: 'تم حفظ التعديلات وتحديث المستودع بنجاح! 🎉',
    saveError: 'فشل حفظ التعديلات. يرجى التحقق من اتصالك.',
    remoteOnly: 'عمل عن بعد فقط',
    visaReq: 'يتطلب تأشيرة / رعاية',
    minScore: 'الحد الأدنى للقبول (AI)',
    activeState: 'نشط',
    pausedState: 'متوقف مؤقتاً',
    noExclusions: 'لا توجد كلمات مستبعدة حالياً',
  },
  en: {
    title: 'Search Settings & CV',
    globalConfigTitle: 'Global Search Settings',
    jobTitles: 'Target Job Titles',
    experience: 'Years of Experience',
    exclusions: 'Exclusion Keywords',
    frequency: 'Scan Frequency',
    countriesTitle: 'Country Filtering Rules',
    cvTitle: 'Resume (CV)',
    currentCv: 'Current file:',
    replaceCvBtn: 'Replace Resume File',
    saveSettingsBtn: 'Save All Changes',
    saveSuccess: 'Settings saved & repository updated successfully! 🎉',
    saveError: 'Failed to save settings. Please verify connectivity.',
    remoteOnly: 'Remote Only',
    visaReq: 'Requires Visa',
    minScore: 'Min Match Score (AI)',
    activeState: 'Active',
    pausedState: 'Paused',
    noExclusions: 'No exclusion keywords configured',
  }
};

export default function DashboardSettings({
  config,
  setConfig,
  repoName,
  githubToken,
  language,
  onReSetup,
  chatId,
  cvFileName,
  setCvFileName
}: DashboardSettingsProps) {
  const t = TRANSLATIONS[language];

  // Config mapping fallback
  const globalSearch = config?.global_search || {};
  const currentJobTitles = globalSearch.job_titles || [];
  const currentYearsExp = globalSearch.years_of_experience || '';
  const currentExclusions = globalSearch.exclude_keywords || [];
  const currentFreq = globalSearch.scan_frequency || '20m';

  const [countries, setCountries] = useState<TargetCountryConfig[]>(config?.target_countries || []);
  const [newCvFile, setNewCvFile] = useState<{ name: string; base64: string } | null>(null);
  const [saveLoading, setSaveLoading] = useState(false);
  const [toastMsg, setToastMsg] = useState<{ success: boolean; text: string } | null>(null);

  // Parse frequency display
  const getFrequencyLabel = (val: string) => {
    if (val === '20m') return language === 'ar' ? 'كل 20 دقيقة' : 'Every 20 mins';
    if (val === '1h') return language === 'ar' ? 'كل ساعة' : 'Every 1 hour';
    if (val === '6h') return language === 'ar' ? 'كل 6 ساعات' : 'Every 6 hours';
    return language === 'ar' ? 'مرة واحدة يومياً' : 'Once daily';
  };

  // Local helper to toggle active/pause per country
  const toggleCountryActive = (countryId: string) => {
    setCountries(countries.map(c => 
      c.country === countryId ? { ...c, active: !c.active } : c
    ));
  };

  // Local helper to change country properties
  const updateCountryRule = (countryId: string, updates: Partial<TargetCountryConfig>) => {
    setCountries(countries.map(c => 
      c.country === countryId ? { ...c, ...updates } : c
    ));
  };

  // Handle local CV Upload
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      setToastMsg({ success: false, text: language === 'ar' ? 'حجم الملف يجب أن يقل عن 2 ميجابايت' : 'File must be under 2MB' });
      return;
    }
    const reader = new FileReader();
    reader.onload = (event) => {
      const result = event.target?.result as string;
      const base64 = result.split(',')[1];
      setNewCvFile({ name: file.name, base64 });
      setToastMsg(null);
    };
    reader.readAsDataURL(file);
  };

  // Save changes to GitHub repo
  const handleSaveAll = async () => {
    setSaveLoading(true);
    setToastMsg(null);

    const updatedConfig = {
      ...config,
      target_countries: countries
    };

    const fileExt = newCvFile?.name ? (newCvFile.name.split('.').pop() || 'pdf') : '';
    const cvFilenameOnRepo = newCvFile?.name ? `default_cv.${fileExt}` : undefined;

    try {
      const res = await fetch('/api/setup/write-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          github_token: githubToken,
          repo_name: repoName,
          config_data: updatedConfig,
          cv_filename: cvFilenameOnRepo,
          cv_base64: newCvFile?.base64 || undefined
        })
      });

      if (res.ok) {
        setConfig(updatedConfig);
        if (newCvFile) {
          setCvFileName(newCvFile.name);
          setNewCvFile(null);
        }
        setToastMsg({ success: true, text: t.saveSuccess });
      } else {
        throw new Error();
      }
    } catch (e) {
      setToastMsg({ success: false, text: t.saveError });
    } finally {
      setSaveLoading(false);
    }
  };

  return (
    <div className="space-y-6 text-start">
      
      {/* Toast Alert */}
      {toastMsg && (
        <div className={`p-4 rounded-xl border text-xs flex items-center gap-2 transition-all ${
          toastMsg.success 
            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
            : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
        }`}>
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{toastMsg.text}</span>
        </div>
      )}

      {/* ─── ROW 1: READ-ONLY GLOBAL PREFERENCES ─── */}
      <div className="p-5 rounded-2xl border border-white/[0.04] bg-[#030712]/40 space-y-4">
        <div className="flex items-center justify-between border-b border-white/[0.04] pb-3">
          <h4 className="text-sm font-bold text-white flex items-center gap-2">
            <Sliders className="h-4 w-4 text-blue-400" />
            {t.globalConfigTitle}
          </h4>
          <button
            onClick={onReSetup}
            className="text-[11px] font-bold text-blue-400 hover:text-blue-300 border border-blue-500/20 bg-blue-500/5 px-2.5 py-1 rounded hover:scale-[1.02] active:scale-[0.98] transition-all"
          >
            {language === 'ar' ? 'تعديل شامل للكل' : 'Re-run Wizard'}
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          {/* Job Titles */}
          <div>
            <span className="text-slate-500 block mb-1.5">{t.jobTitles}</span>
            <div className="flex flex-wrap gap-1.5">
              {currentJobTitles.map((title: string) => (
                <span key={title} className="bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded text-[11px]">
                  {title}
                </span>
              ))}
            </div>
          </div>

          {/* Experience & Frequency */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="text-slate-500 block mb-1">{t.experience}</span>
              <span className="text-slate-200 font-semibold">{currentYearsExp}</span>
            </div>
            <div>
              <span className="text-slate-500 block mb-1">{t.frequency}</span>
              <span className="text-slate-200 font-semibold">{getFrequencyLabel(currentFreq)}</span>
            </div>
          </div>

          {/* Exclusion Keywords */}
          <div className="md:col-span-2">
            <span className="text-slate-500 block mb-1.5">{t.exclusions}</span>
            {currentExclusions.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {currentExclusions.map((kw: string) => (
                  <span key={kw} className="bg-white/5 text-slate-300 border border-white/10 px-2 py-0.5 rounded text-[11px] font-mono">
                    {kw}
                  </span>
                ))}
              </div>
            ) : (
              <span className="text-slate-500 italic text-[11px]">{t.noExclusions}</span>
            )}
          </div>
        </div>
      </div>

      {/* ─── ROW 2: CV QUICK-REPLACE WIDGET ─── */}
      <div className="p-5 rounded-2xl border border-white/[0.04] bg-[#030712]/40 space-y-4">
        <h4 className="text-sm font-bold text-white flex items-center gap-2 border-b border-white/[0.04] pb-3">
          <FileText className="h-4 w-4 text-orange-400" />
          {t.cvTitle}
        </h4>
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white/[0.01] p-3 rounded-lg border border-white/[0.04]">
          <div className="flex items-center gap-2.5 text-xs">
            <div className="h-9 w-9 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400 shrink-0">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <span className="text-slate-500 block text-[10px]">{t.currentCv}</span>
              <span className="text-slate-200 font-semibold font-mono truncate max-w-[200px] block font-sans">
                {newCvFile ? newCvFile.name : (cvFileName || 'default_cv.pdf')}
              </span>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <label className="h-8 px-3 rounded-lg border border-white/[0.08] hover:bg-white/[0.04] text-[11px] font-bold text-slate-300 transition-all flex items-center justify-center gap-1 cursor-pointer">
              <Upload className="h-3.5 w-3.5" />
              {t.replaceCvBtn}
              <input
                type="file"
                accept=".pdf,.docx"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>
            {newCvFile && (
              <button
                onClick={() => setNewCvFile(null)}
                className="h-8 w-8 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 flex items-center justify-center transition-all"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* ─── ROW 3: TARGET COUNTRIES OVERRIDES & PAUSE/RESUME ─── */}
      <div className="p-5 rounded-2xl border border-white/[0.04] bg-[#030712]/40 space-y-4">
        <h4 className="text-sm font-bold text-white flex items-center gap-2 border-b border-white/[0.04] pb-3">
          <Globe className="h-4 w-4 text-emerald-400" />
          {t.countriesTitle}
        </h4>

        {/* Scrollable Container with Max Height */}
        <div className="space-y-3 max-h-[280px] overflow-y-auto pr-1 [&::-webkit-scrollbar]:w-1 [&::-webkit-scrollbar-track]:bg-white/[0.01] [&::-webkit-scrollbar-thumb]:bg-white/10 [&::-webkit-scrollbar-thumb]:rounded-full">
          {countries.map((c) => (
            <div 
              key={c.country} 
              className={`p-3.5 rounded-xl border transition-all ${
                c.active 
                  ? 'border-white/[0.06] bg-[#050b18]/60 hover:border-white/[0.1]' 
                  : 'border-white/[0.03] bg-white/[0.01] opacity-60'
              }`}
            >
              {/* Card Header */}
              <div className="flex items-center justify-between pb-2.5 border-b border-white/[0.04] mb-2.5">
                <div className="flex items-center gap-2 text-xs font-bold text-white">
                  <span className="text-[9px] font-mono font-bold bg-white/10 border border-white/10 px-1.5 py-0.5 rounded text-slate-400 uppercase select-none">
                    {c.country.substring(0, 2).toUpperCase()}
                  </span>
                  <span>{c.country}</span>
                </div>
                
                {/* Individual Pause/Resume Switch */}
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-bold ${c.active ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {c.active ? t.activeState : t.pausedState}
                  </span>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input 
                      type="checkbox" 
                      checked={c.active} 
                      onChange={() => toggleCountryActive(c.country)}
                      className="sr-only peer"
                    />
                    <div className="w-8 h-4.5 bg-white/[0.08] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:right-[2px] peer-checked:after:right-[14px] after:bg-slate-400 peer-checked:after:bg-blue-400 after:rounded-full after:h-3.5 after:w-3.5 after:transition-all peer-checked:bg-blue-500/25 border border-white/[0.08]" />
                  </label>
                </div>
              </div>

              {/* Card Controls Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                
                {/* Toggles */}
                <div className="space-y-2">
                  {/* Remote Only */}
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] text-slate-400 flex items-center gap-1.5 font-sans">
                      <Laptop className="h-3 w-3 text-blue-400" />
                      {t.remoteOnly}
                    </span>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={c.remote_only} 
                        disabled={!c.active}
                        onChange={(e) => updateCountryRule(c.country, { remote_only: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-7 h-4 bg-white/[0.06] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:right-[2px] peer-checked:after:right-[12px] after:bg-slate-500 peer-checked:after:bg-blue-400 after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-blue-500/25 border border-white/[0.08] disabled:opacity-40" />
                    </label>
                  </div>

                  {/* Requires Visa (Hidden for Worldwide) */}
                  {c.country !== 'Worldwide' && (
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-slate-400 flex items-center gap-1.5 font-sans">
                        <Shield className="h-3 w-3 text-purple-400" />
                        {t.visaReq}
                      </span>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={c.requires_visa} 
                          disabled={!c.active || c.country === 'Egypt'}
                          onChange={(e) => updateCountryRule(c.country, { requires_visa: e.target.checked })}
                          className="sr-only peer"
                        />
                        <div className="w-7 h-4 bg-white/[0.06] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:right-[2px] peer-checked:after:right-[12px] after:bg-slate-500 peer-checked:after:bg-blue-400 after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-blue-500/25 border border-white/[0.08] disabled:opacity-40" />
                      </label>
                    </div>
                  )}
                </div>

                {/* Score Slider */}
                <div className="space-y-1">
                  <div className="flex justify-between items-center text-[11px] font-sans">
                    <span className="text-slate-400 flex items-center gap-1.5">
                      <Target className="h-3 w-3 text-orange-400" />
                      {t.minScore}
                    </span>
                    <span className="text-blue-400 font-bold">{c.min_match_score}%</span>
                  </div>
                  <input
                    type="range"
                    min="50"
                    max="95"
                    value={c.min_match_score}
                    disabled={!c.active}
                    onChange={(e) => updateCountryRule(c.country, { min_match_score: parseInt(e.target.value) })}
                    className="w-full h-1 rounded-lg bg-white/[0.08] appearance-none cursor-pointer accent-blue-500 disabled:opacity-40"
                  />
                </div>

              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Save Button */}
      <button
        onClick={handleSaveAll}
        disabled={saveLoading}
        className="w-full h-10 rounded-md bg-blue-600 hover:bg-blue-700 hover:scale-[1.02] active:scale-[0.98] transition-all text-white font-bold text-xs flex items-center justify-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 font-sans"
      >
        {saveLoading ? (
          <RotateCw className="h-3.5 w-3.5 animate-spin" />
        ) : (
          <Check className="h-4 w-4" />
        )}
        {t.saveSettingsBtn}
      </button>

    </div>
  );
}

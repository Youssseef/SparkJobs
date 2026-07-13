import React from 'react';
import { Upload, FileText, ArrowRight } from 'lucide-react';

interface CvUploadPanelProps {
  language: 'ar' | 'en';
  cvFileName: string;
  coverLetterText: string;
  onChangeCv: (fileName: string, base64: string) => void;
  onChangeCoverLetter: (text: string) => void;
  onError: (msg: string) => void;
  onBack: () => void;
  onNext: () => void;
}

export default function CvUploadPanel({
  language,
  cvFileName,
  coverLetterText,
  onChangeCv,
  onChangeCoverLetter,
  onError,
  onBack,
  onNext
}: CvUploadPanelProps) {
  const t = {
    ar: {
      cvLabel: 'رفع السيرة الذاتية',
      cvUploadPlaceholder: 'اختر ملف PDF أو Word (.pdf, .docx)',
      coverLetterLabel: 'خطاب التقديم (اختياري)',
      coverLetterPlaceholder: 'الصق هنا خطاب تقديم سابق لمساعدة الذكاء الاصطناعي في مطابقة أسلوبك...',
      fileSelected: 'الملف المحدد:',
      backBtn: 'الرجوع',
      nextBtn: 'المتابعة للخطوة التالية',
    },
    en: {
      cvLabel: 'Upload Resume / CV',
      cvUploadPlaceholder: 'Select a PDF or Word file (.pdf, .docx)',
      coverLetterLabel: 'Cover Letter (Optional)',
      coverLetterPlaceholder: 'Paste a previous cover letter here to help the AI match your writing style...',
      fileSelected: 'Selected file:',
      backBtn: 'Back',
      nextBtn: 'Continue to Next Step',
    }
  }[language];

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      onError(language === 'ar' ? 'حجم الملف كبير جداً. يجب أن يكون أقل من 2 ميجابايت.' : 'File is too large. Max size is 2MB.');
      return;
    }
    onError('');
    const reader = new FileReader();
    reader.onload = (event) => {
      const result = event.target?.result as string;
      const base64 = result.split(',')[1];
      onChangeCv(file.name, base64);
    };
    reader.readAsDataURL(file);
  };

  return (
    <div className="space-y-6 text-start">
      {/* CV File Upload */}
      <div>
        <label className="block text-slate-300 text-xs font-bold mb-2">{t.cvLabel}</label>
        <div className="flex items-center justify-center w-full">
          <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-lg cursor-pointer border-white/[0.08] bg-[#030712] hover:bg-[#050b18] hover:border-blue-500/50 transition-all">
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              {cvFileName ? (
                <FileText className="h-8 w-8 text-blue-400 mb-2" />
              ) : (
                <Upload className="h-8 w-8 text-slate-500 mb-2" />
              )}
              <p className="text-xs text-slate-400 font-semibold mb-1 px-4 text-center truncate max-w-sm">
                {cvFileName ? `${t.fileSelected} ${cvFileName}` : t.cvUploadPlaceholder}
              </p>
            </div>
            <input
              type="file"
              accept=".pdf,.docx"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Cover Letter Input */}
      <div>
        <label className="block text-slate-300 text-xs font-bold mb-2">{t.coverLetterLabel}</label>
        <textarea
          value={coverLetterText}
          onChange={(e) => onChangeCoverLetter(e.target.value)}
          placeholder={t.coverLetterPlaceholder}
          rows={5}
          className={`w-full p-4 rounded-md border border-white/[0.08] bg-[#030712] text-xs text-slate-100 placeholder-slate-600 focus:ring-1 focus:ring-blue-500 outline-none resize-none [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-white/[0.02] [&::-webkit-scrollbar-thumb]:bg-white/10 [&::-webkit-scrollbar-thumb]:rounded-full ${language === 'ar' ? 'text-right' : 'text-left'}`}
          dir={language === 'ar' ? 'rtl' : 'ltr'}
        />
      </div>

      <div className="flex gap-4 mt-8">
        <button
          onClick={onBack}
          className="flex-1 h-10 rounded-md border border-white/[0.08] hover:bg-white/[0.04] text-slate-300 text-sm transition-all"
        >
          {t.backBtn}
        </button>
        <button
          onClick={onNext}
          className="flex-1 h-10 rounded-md bg-blue-600 hover:bg-blue-700 hover:scale-[1.02] active:scale-[0.98] transition-all text-white font-semibold text-sm flex items-center justify-center gap-2"
        >
          {t.nextBtn}
          <ArrowRight className={`h-4 w-4 ${language === 'ar' ? 'rotate-180' : ''}`} />
        </button>
      </div>
    </div>
  );
}

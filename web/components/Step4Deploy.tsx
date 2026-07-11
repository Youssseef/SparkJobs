import React, { useState } from 'react';
import { HelpCircle } from 'lucide-react';

interface Step4DeployProps {
  language: 'ar' | 'en';
  t: any;
  GUIDE_COMPONENTS: any;
  githubToken: string;
  setGithubToken: (token: string) => void;
  githubRepo: string;
  setGithubRepo: (repo: string) => void;
  onBack: () => void;
  onDeploy: () => void;
}

export default function Step4Deploy({
  language,
  t,
  GUIDE_COMPONENTS,
  githubToken,
  setGithubToken,
  githubRepo,
  setGithubRepo,
  onBack,
  onDeploy
}: Step4DeployProps) {
  const [activeHelp, setActiveHelp] = useState<string | null>(null);

  const hasGithubSettings = githubToken.trim() !== '' && githubRepo.trim() !== '';

  return (
    <div className="space-y-5 text-start">
      
      {/* GitHub Token */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-slate-300 text-xs font-bold">{t.githubTokenLabel}</label>
          <button 
            onClick={() => setActiveHelp(activeHelp === 'github' ? null : 'github')}
            className="text-blue-400 text-[10px] font-semibold flex items-center gap-1 hover:underline"
          >
            <HelpCircle className="h-3 w-3" />
            {t.helpLinkPat}
          </button>
        </div>
        {activeHelp === 'github' && (
          <div className="p-3 mb-2 rounded bg-white/[0.03] border border-white/[0.05] text-[11px] text-slate-400 leading-relaxed">
            {GUIDE_COMPONENTS.github}
          </div>
        )}
        <input
          type="password"
          value={githubToken}
          onChange={(e) => setGithubToken(e.target.value)}
          placeholder="ghp_..."
          className="w-full h-10 px-4 rounded-md border border-white/[0.08] bg-[#030712] text-sm text-slate-100 placeholder-slate-600 focus:ring-1 focus:ring-blue-500 outline-none"
        />
      </div>

      {/* GitHub Repository Name */}
      <div>
        <label className="block text-slate-300 text-xs font-bold mb-2">{t.githubRepoLabel}</label>
        <input
          type="text"
          value={githubRepo}
          onChange={(e) => setGithubRepo(e.target.value.replace(/[^a-zA-Z0-9-_]/g, ''))}
          placeholder="sparkjobs-alerts"
          className="w-full h-10 px-4 rounded-md border border-white/[0.08] bg-[#030712] text-sm text-slate-100 placeholder-slate-600 focus:ring-1 focus:ring-blue-500 outline-none"
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
          onClick={onDeploy}
          disabled={!hasGithubSettings}
          className="flex-1 h-10 rounded-md bg-blue-600 hover:bg-blue-700 hover:scale-[1.02] active:scale-[0.98] transition-all text-white font-semibold text-sm flex items-center justify-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
        >
          {t.deployBtn}
        </button>
      </div>

    </div>
  );
}

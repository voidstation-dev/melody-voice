"use client";
import { useState, useRef, useEffect } from "react";
import { Voice } from "@/types/voice";
import { RefreshCcw, Trash2, Info, ChevronDown, Check, Download } from "lucide-react";

type VoiceSettingsPanelProps = {
  voices: Voice[];
  selectedVoice: string;
  onSelectVoice: (v: string) => void;
  rate: number;
  onRateChange: (r: number) => void;
  onGenerate: () => void;
  isSubmitting: boolean;
  activeJob?: any;
  fakeProgress?: number;
};

const CustomSlider = ({
  label,
  left,
  right,
  value,
  onChange,
  min = 0,
  max = 2,
  step = 0.1,
}: any) => (
  <div className="flex flex-col gap-1">
    <div className="flex items-center justify-between">
      <span className="text-sm font-bold text-foreground">{label}</span>
      <div className="relative flex h-2 w-full max-w-[140px] items-center rounded-full bg-muted ml-4">
        <div
          className="h-full rounded-full bg-primary pointer-events-none"
          style={{ width: `${((value - min) / (max - min)) * 100}%` }}
        />
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange && onChange(parseFloat(e.target.value))}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
      </div>
    </div>
    <div className="flex items-center justify-between text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
      <span>{left}</span>
      <span>{right}</span>
    </div>
  </div>
);

export function VoiceSettingsPanel({
  voices,
  selectedVoice,
  onSelectVoice,
  rate,
  onRateChange,
  onGenerate,
  isSubmitting,
  activeJob,
  fakeProgress,
}: VoiceSettingsPanelProps) {
  const currentVoice = voices.find((v) => v.voiceType === selectedVoice);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h3 className="text-xs font-extrabold uppercase tracking-widest text-muted-foreground mb-4">
          Selected Voice
        </h3>

        <div className="relative" ref={dropdownRef}>
          <div
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className={`relative rounded-2xl bg-card p-5 border ${isDropdownOpen ? "border-primary" : "border-border"} cursor-pointer hover:border-primary transition-colors`}
          >
            <div className="mb-4 flex items-center justify-between">
              <span className="rounded-md bg-[#ffece0] px-2 py-1 text-[10px] font-bold text-[#d96623]">
                CLICK TO CHANGE
              </span>
              <ChevronDown
                className={`h-5 w-5 text-muted-foreground transition-transform ${isDropdownOpen ? "rotate-180" : ""}`}
              />
            </div>

            <div className="flex items-start justify-between">
              <div className="flex items-center gap-4">
                <div className="h-14 w-14 rounded-2xl bg-muted/60 overflow-hidden flex items-center justify-center flex-shrink-0 p-2.5">
                   <div className="h-full w-full bg-[#1a1a1a] rounded-full relative">
                    <div className="absolute top-1/2 left-0 h-4 w-2 bg-[#1a1a1a] rounded-r-md -ml-1"></div>
                    <div className="absolute top-1/2 right-0 h-4 w-2 bg-[#1a1a1a] rounded-l-md -mr-1"></div>
                  </div>
                </div>
                <div className="flex flex-col gap-0.5">
                  <div className="text-lg font-bold text-foreground line-clamp-1">
                    {currentVoice?.displayName || "Select a voice"}
                  </div>
                  <div className="text-sm font-medium text-muted-foreground line-clamp-1">
                    {currentVoice?.languageCode || "No voice selected"}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Custom Dropdown Menu */}
          {isDropdownOpen && (
            <div className="absolute top-full left-0 right-0 mt-2 z-50 max-h-[300px] overflow-y-auto rounded-xl border border-border bg-card p-2 shadow-xl">
              {voices.length === 0 ? (
                <div className="p-4 text-center text-sm text-muted-foreground">
                  Loading voices...
                </div>
              ) : (
                voices.map((v) => (
                  <div
                    key={v.voiceType}
                    onClick={() => {
                      onSelectVoice(v.voiceType);
                      setIsDropdownOpen(false);
                    }}
                    className={`flex items-center justify-between rounded-lg px-3 py-2 text-sm cursor-pointer transition-colors ${
                      selectedVoice === v.voiceType
                        ? "bg-primary text-primary-foreground font-medium"
                        : "hover:bg-muted text-foreground"
                    }`}
                  >
                    <div className="flex flex-col">
                      <span>{v.displayName}</span>
                      <span
                        className={`text-[10px] ${selectedVoice === v.voiceType ? "text-primary-foreground/80" : "text-muted-foreground"}`}
                      >
                        {v.languageCode}
                      </span>
                    </div>
                    {selectedVoice === v.voiceType && (
                      <Check className="h-4 w-4" />
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-[10px] font-extrabold uppercase tracking-wider text-muted-foreground">
            Tone Properties
          </h3>
        </div>

        <div className="space-y-4">
          <CustomSlider
            label="Speed"
            left="Slower"
            right="Faster"
            min={0.5}
            max={2.0}
            step={0.1}
            value={rate}
            onChange={onRateChange}
          />
        </div>
      </div>

      {/* Generation Status Block */}
      {activeJob && (
        <div className="rounded-2xl border border-border bg-card p-5 shadow-sm mt-4">
          <div className="flex items-center justify-between mb-4">
            <span className="text-[10px] font-extrabold uppercase tracking-wider text-muted-foreground">Generation Status</span>
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
              activeJob.status === 'completed' ? 'bg-green-100 text-green-700' :
              activeJob.status === 'failed' ? 'bg-red-100 text-red-700' : 'bg-[#ffece0] text-[#d96623]'
            }`}>
              {activeJob.status === 'processing' || activeJob.status === 'queued' ? 'PROCESSING' : activeJob.status.toUpperCase()}
            </span>
          </div>
          
          {(activeJob.status === 'queued' || activeJob.status === 'processing') && (
            <div className="space-y-3">
              <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary rounded-full transition-all duration-300 ease-out" 
                  style={{ width: `${activeJob.progress ?? fakeProgress}%` }}
                ></div>
              </div>
              <div className="flex items-center justify-between">
                <p className="text-xs text-muted-foreground animate-pulse font-medium">
                  Synthesizing voice... 
                </p>
                <span className="text-xs font-bold text-foreground">
                  {activeJob.progress ?? fakeProgress}%
                </span>
              </div>
            </div>
          )}

          {activeJob.status === 'failed' && (
            <p className="text-xs text-red-600 font-medium">
              {activeJob.errorMessage || "An error occurred during generation. Please try again."}
            </p>
          )}
          
          {activeJob.status === 'completed' && activeJob.audioUrl && (
            <div className="flex flex-col gap-3 pt-2">
              <audio controls src={`http://localhost:8000${activeJob.audioUrl}`} className="h-8 w-full" autoPlay />
              <a 
                href={`http://localhost:8000${activeJob.audioUrl}`}
                download={`CapVoice_${activeJob.id}.mp3`}
                className="flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-xs font-bold text-primary-foreground hover:opacity-90 transition-colors"
              >
                <Download className="h-4 w-4" />
                Download MP3
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

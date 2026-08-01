"use client";
import { useState, useRef, useEffect } from "react";
import { Voice } from "@/types/voice";
import { RefreshCcw, Trash2, Info, ChevronDown, Check, Download } from "lucide-react";
import { resolveApiUrl } from "@/lib/api-client";

type VoiceSettingsPanelProps = {
  voices: Voice[];
  selectedVoice: string;
  onSelectVoice: (v: string) => void;
  rate: number;
  onRateChange: (r: number) => void;
  onGenerate: () => void;
  isSubmitting: boolean;
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
}: any) => {
  const percentage = ((value - min) / (max - min)) * 100;
  
  return (
    <div className="flex flex-col gap-4 p-4 rounded-2xl bg-card border border-border shadow-sm">
      <div className="flex items-center justify-between">
        <span className="text-sm font-bold text-foreground">{label}</span>
        <div className="px-2 py-1 rounded-md bg-primary/10 text-primary text-xs font-bold">
          {value.toFixed(1)}x
        </div>
      </div>
      
      <div className="relative flex items-center h-6 w-full">
        {/* Track background */}
        <div className="absolute w-full h-1.5 top-1/2 -translate-y-1/2 rounded-full bg-muted pointer-events-none" />
        {/* Track fill */}
        <div 
          className="absolute h-1.5 top-1/2 -translate-y-1/2 rounded-full bg-primary pointer-events-none"
          style={{ width: `${percentage}%` }}
        />
        {/* Custom Thumb */}
        <div 
          className="absolute h-4 w-4 bg-background border-2 border-primary rounded-full shadow-md pointer-events-none"
          style={{ left: `calc(${percentage}% - 8px)` }}
        />
        {/* Interactive Invisible Input */}
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange && onChange(parseFloat(e.target.value))}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
        />
      </div>
      
      <div className="flex items-center justify-between text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
        <span>{left}</span>
        <span>{right}</span>
      </div>
    </div>
  );
};

export function VoiceSettingsPanel({
  voices,
  selectedVoice,
  onSelectVoice,
  rate,
  onRateChange,
  onGenerate,
  isSubmitting,
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
            className={`group flex items-center justify-between rounded-2xl bg-card p-3 border transition-all cursor-pointer ${
              isDropdownOpen 
                ? "border-primary ring-4 ring-primary/10 shadow-sm" 
                : "border-border hover:border-primary/50 hover:shadow-sm"
            }`}
          >
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary/15">
                <div className="relative flex items-center justify-center">
                  <div className="h-5 w-5 bg-current rounded-full" />
                  <div className="absolute top-1/2 -left-1 h-2 w-1 bg-current rounded-r-md -translate-y-1/2" />
                  <div className="absolute top-1/2 -right-1 h-2 w-1 bg-current rounded-l-md -translate-y-1/2" />
                </div>
              </div>
              <div className="flex flex-col">
                <span className="text-base font-bold text-foreground">
                  {currentVoice?.displayName || "Select a voice"}
                </span>
                <span className="text-xs font-medium text-muted-foreground">
                  {currentVoice?.languageCode || "No voice selected"}
                </span>
              </div>
            </div>
            
            <div className="flex items-center gap-3 pr-2">
              <span className="hidden sm:block text-[10px] font-bold uppercase tracking-wider text-primary opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                Change
              </span>
              <div className={`p-1 rounded-full transition-colors ${isDropdownOpen ? "bg-primary/10 text-primary" : "text-muted-foreground group-hover:text-foreground"}`}>
                <ChevronDown
                  className={`h-4 w-4 transition-transform duration-200 ${isDropdownOpen ? "rotate-180" : ""}`}
                />
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
    </div>
  );
}

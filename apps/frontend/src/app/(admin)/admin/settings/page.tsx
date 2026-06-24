"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type SiteConfig } from "@/lib/api";
import { Alert, PageSpinner, Button } from "@/components/ui/index";
import { Sun, Moon, Save } from "lucide-react";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<"theme" | "content">("theme");
  const [changes, setChanges] = useState<Partial<SiteConfig>>({});
  const [hasChanges, setHasChanges] = useState(false);

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-config"],
    queryFn: () => api.admin.config(),
  });

  const config = data?.config;

  const updateMutation = useMutation({
    mutationFn: (data: Partial<SiteConfig>) => api.admin.updateConfig(data),
    onSuccess: (result) => {
      queryClient.setQueryData(["admin-config"], { config: result.config });
      setChanges({});
      setHasChanges(false);
    },
  });

  const handleChange = (path: string, value: unknown) => {
    const newChanges = { ...changes };
    const keys = path.split(".");
    let current: any = newChanges;

    for (let i = 0; i < keys.length - 1; i++) {
      const key = keys[i];
      if (!current[key]) current[key] = {};
      current = current[key];
    }

    current[keys[keys.length - 1]] = value;
    setChanges(newChanges);
    setHasChanges(true);
  };

  const handleSave = async () => {
    updateMutation.mutate(changes);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <PageSpinner />
      </div>
    );
  }

  if (error || !config) {
    return (
      <Alert type="error">
        Failed to load site settings. Please try again.
      </Alert>
    );
  }

  const theme = { ...config.theme, ...(changes.theme || {}) };
  const content = { ...config.content, ...(changes.content || {}) };

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="heading-section">Site Settings</h1>
        <p className="text-[var(--color-muted)] mt-1">
          Customize your site's appearance and content
        </p>
      </div>

      {/* Tabs */}
      <div className="card mb-6">
        <div className="flex gap-4 border-b border-[var(--color-border)]">
          <button
            onClick={() => setActiveTab("theme")}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === "theme"
                ? "border-primary text-primary"
                : "border-transparent text-[var(--color-muted)] hover:text-[var(--color-text)]"
            }`}
          >
            Theme & Appearance
          </button>
          <button
            onClick={() => setActiveTab("content")}
            className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
              activeTab === "content"
                ? "border-primary text-primary"
                : "border-transparent text-[var(--color-muted)] hover:text-[var(--color-text)]"
            }`}
          >
            Content
          </button>
        </div>
      </div>

      {/* Theme Tab */}
      {activeTab === "theme" && (
        <div className="space-y-6">
          {/* Mode Toggle */}
          <div className="card">
            <h2 className="font-display text-lg text-[var(--color-text)] mb-4">
              Theme Mode
            </h2>
            <div className="flex gap-4">
              <button
                onClick={() => handleChange("theme.mode", "light")}
                className={`flex items-center gap-2 px-4 py-3 rounded-lg border-2 transition-all ${
                  theme.mode === "light"
                    ? "border-primary bg-primary/5"
                    : "border-[var(--color-border)] hover:border-primary"
                }`}
              >
                <Sun className="w-5 h-5" />
                <span className="font-medium">Light</span>
              </button>
              <button
                onClick={() => handleChange("theme.mode", "dark")}
                className={`flex items-center gap-2 px-4 py-3 rounded-lg border-2 transition-all ${
                  theme.mode === "dark"
                    ? "border-primary bg-primary/5"
                    : "border-[var(--color-border)] hover:border-primary"
                }`}
              >
                <Moon className="w-5 h-5" />
                <span className="font-medium">Dark</span>
              </button>
            </div>
          </div>

          {/* Colors */}
          <div className="card">
            <h2 className="font-display text-lg text-[var(--color-text)] mb-4">
              Colors
            </h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <ColorField
                label="Primary Color"
                value={theme.primaryColor}
                onChange={(val) => handleChange("theme.primaryColor", val)}
              />
              <ColorField
                label="Accent Color"
                value={theme.accentColor}
                onChange={(val) => handleChange("theme.accentColor", val)}
              />
              <ColorField
                label="Background Color"
                value={theme.backgroundColor || "#faf7f4"}
                onChange={(val) => handleChange("theme.backgroundColor", val)}
              />
              <ColorField
                label="Text Color"
                value={theme.textColor || "#2c2c2c"}
                onChange={(val) => handleChange("theme.textColor", val)}
              />
            </div>
          </div>

          {/* Fonts */}
          <div className="card">
            <h2 className="font-display text-lg text-[var(--color-text)] mb-4">
              Fonts
            </h2>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
                  Display Font (Headings)
                </label>
                <input
                  type="text"
                  value={theme.fontDisplay}
                  onChange={(e) => handleChange("theme.fontDisplay", e.target.value)}
                  placeholder="e.g. Cormorant Garamond"
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
                  Body Font (Text)
                </label>
                <input
                  type="text"
                  value={theme.fontBody}
                  onChange={(e) => handleChange("theme.fontBody", e.target.value)}
                  placeholder="e.g. DM Sans"
                  className="input w-full"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content Tab */}
      {activeTab === "content" && (
        <div className="space-y-6">
          {/* Hero Content */}
          <div className="card">
            <h2 className="font-display text-lg text-[var(--color-text)] mb-4">
              Hero Section
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
                  Title
                </label>
                <input
                  type="text"
                  value={content.hero?.en?.title || ""}
                  onChange={(e) =>
                    handleChange("content.hero.en.title", e.target.value)
                  }
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
                  Subtitle
                </label>
                <input
                  type="text"
                  value={content.hero?.en?.subtitle || ""}
                  onChange={(e) =>
                    handleChange("content.hero.en.subtitle", e.target.value)
                  }
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
                  CTA Button Text
                </label>
                <input
                  type="text"
                  value={content.hero?.en?.cta || ""}
                  onChange={(e) =>
                    handleChange("content.hero.en.cta", e.target.value)
                  }
                  className="input w-full"
                />
              </div>
            </div>
          </div>

          {/* About Content */}
          <div className="card">
            <h2 className="font-display text-lg text-[var(--color-text)] mb-4">
              About Section
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
                  Title
                </label>
                <input
                  type="text"
                  value={content.about?.en?.title || ""}
                  onChange={(e) =>
                    handleChange("content.about.en.title", e.target.value)
                  }
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
                  Description
                </label>
                <textarea
                  value={content.about?.en?.body || ""}
                  onChange={(e) =>
                    handleChange("content.about.en.body", e.target.value)
                  }
                  rows={4}
                  className="input w-full"
                />
              </div>
            </div>
          </div>

          {/* Contact Information */}
          <div className="card">
            <h2 className="font-display text-lg text-[var(--color-text)] mb-4">
              Contact Information
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
                  Address
                </label>
                <input
                  type="text"
                  value={content.contact?.address || ""}
                  onChange={(e) =>
                    handleChange("content.contact.address", e.target.value)
                  }
                  className="input w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
                  Phone
                </label>
                <input
                  type="tel"
                  value={content.contact?.phone || ""}
                  onChange={(e) =>
                    handleChange("content.contact.phone", e.target.value)
                  }
                  className="input w-full"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Save Button */}
      {hasChanges && (
        <div className="fixed bottom-6 right-6 bg-white dark:bg-slate-800 rounded-lg shadow-lg p-4 flex items-center gap-4">
          <Alert type="info" className="m-0">
            You have unsaved changes
          </Alert>
          <Button
            onClick={handleSave}
            loading={updateMutation.isPending}
            className="flex items-center gap-2"
          >
            <Save className="w-4 h-4" />
            Save Changes
          </Button>
        </div>
      )}
    </div>
  );
}

function ColorField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
        {label}
      </label>
      <div className="flex gap-3">
        <input
          type="color"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-16 h-10 rounded border border-[var(--color-border)] cursor-pointer"
        />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="#000000"
          className="input flex-1 font-mono text-sm"
        />
      </div>
    </div>
  );
}


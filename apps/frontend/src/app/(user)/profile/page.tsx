"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, type User } from "@/lib/api";
import { Alert, PageSpinner, Button } from "@/components/ui/index";
import { User as UserIcon, Mail, Phone, Globe, Save } from "lucide-react";
import { useAuthStore } from "@/lib/store";

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuthStore();
  const [changes, setChanges] = useState<Partial<User>>({});
  const [hasChanges, setHasChanges] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  const { data, isLoading, error } = useQuery({
    queryKey: ["user-profile"],
    queryFn: () => api.me.get(),
  });

  const user = data?.user;

  const updateMutation = useMutation({
    mutationFn: (data: Partial<User>) => api.me.update(data),
    onSuccess: (result) => {
      queryClient.setQueryData(["user-profile"], { user: result.user });
      setChanges({});
      setHasChanges(false);
      setSuccessMessage("Profile updated successfully!");
      setTimeout(() => setSuccessMessage(""), 3000);
    },
  });

  const handleChange = (field: keyof User, value: string) => {
    setChanges({ ...changes, [field]: value });
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

  if (error || !user) {
    return (
      <Alert type="error">
        Failed to load profile. Please try again.
      </Alert>
    );
  }

  const displayUser = { ...user, ...changes };

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="heading-section">My Profile</h1>
        <p className="text-[var(--color-muted)] mt-1">
          Manage your account information
        </p>
      </div>

      {/* Success Alert */}
      {successMessage && (
        <div className="mb-6">
          <Alert type="success">{successMessage}</Alert>
        </div>
      )}

      {/* Error Alert */}
      {updateMutation.error && (
        <div className="mb-6">
          <Alert type="error">
            {updateMutation.error instanceof Error
              ? updateMutation.error.message
              : "Failed to update profile"}
          </Alert>
        </div>
      )}

      {/* Profile Form */}
      <div className="card max-w-2xl">
        {/* Avatar Section */}
        <div className="flex items-center gap-6 pb-8 border-b border-[var(--color-border)] mb-8">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary/20 to-primary/10 
                        flex items-center justify-center flex-shrink-0">
            <UserIcon className="w-8 h-8 text-primary" />
          </div>
          <div>
            <div className="font-display text-xl text-[var(--color-text)]">
              {displayUser.firstName} {displayUser.lastName}
            </div>
            <div className="text-sm text-[var(--color-muted)] flex items-center gap-1 mt-1">
              <Mail className="w-4 h-4" />
              {displayUser.email}
            </div>
            {displayUser.verified && (
              <div className="text-xs text-green-600 mt-2">✓ Email verified</div>
            )}
          </div>
        </div>

        {/* Form Fields */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* First Name */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
              First Name
            </label>
            <input
              type="text"
              value={displayUser.firstName}
              onChange={(e) => handleChange("firstName", e.target.value)}
              className="input w-full"
            />
          </div>

          {/* Last Name */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
              Last Name
            </label>
            <input
              type="text"
              value={displayUser.lastName}
              onChange={(e) => handleChange("lastName", e.target.value)}
              className="input w-full"
            />
          </div>

          {/* Phone */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
              <Phone className="w-4 h-4 inline mr-2" />
              Phone Number
            </label>
            <input
              type="tel"
              value={displayUser.phone || ""}
              onChange={(e) => handleChange("phone", e.target.value)}
              placeholder="+1 (555) 000-0000"
              className="input w-full"
            />
          </div>

          {/* Email (Read-only) */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
              <Mail className="w-4 h-4 inline mr-2" />
              Email Address
            </label>
            <input
              type="email"
              value={displayUser.email}
              disabled
              className="input w-full bg-[var(--color-bg-secondary)] cursor-not-allowed"
            />
            <p className="text-xs text-[var(--color-muted)] mt-1">
              Email cannot be changed
            </p>
          </div>

          {/* Language Preference */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
              <Globe className="w-4 h-4 inline mr-2" />
              Preferred Language
            </label>
            <select
              value={displayUser.lang || "en"}
              onChange={(e) => handleChange("lang", e.target.value)}
              className="input w-full"
            >
              <option value="en">English</option>
              <option value="es">Spanish (Español)</option>
              <option value="fr">French (Français)</option>
              <option value="de">German (Deutsch)</option>
              <option value="pt">Portuguese (Português)</option>
            </select>
          </div>

          {/* Role (Read-only) */}
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-[var(--color-text)] mb-2">
              Account Type
            </label>
            <div className="px-4 py-2 rounded-lg bg-[var(--color-bg-secondary)] 
                           border border-[var(--color-border)] text-[var(--color-text)]">
              {displayUser.role === "admin" ? "Admin Account" : "Customer Account"}
            </div>
          </div>
        </div>

        {/* Account Info */}
        <div className="mt-8 pt-6 border-t border-[var(--color-border)]">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-[var(--color-muted)]">Member Since</div>
              <div className="font-medium text-[var(--color-text)]">
                {new Date(displayUser.createdAt).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </div>
            </div>
            <div>
              <div className="text-[var(--color-muted)]">Last Updated</div>
              <div className="font-medium text-[var(--color-text)]">
                {new Date(displayUser.updatedAt).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mt-8 flex gap-4 justify-end">
          {hasChanges ? (
            <>
              <button
                onClick={() => {
                  setChanges({});
                  setHasChanges(false);
                }}
                disabled={updateMutation.isPending}
                className="btn btn-outline"
              >
                Discard Changes
              </button>
              <Button
                onClick={handleSave}
                loading={updateMutation.isPending}
                className="flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Save Changes
              </Button>
            </>
          ) : (
            <div className="text-sm text-[var(--color-muted)]">
              Profile is up to date
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


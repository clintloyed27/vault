"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";
import { UserStats } from "@/types";
import Header from "@/components/Header";
import {
  ShieldCheck,
  User as UserIcon,
  Lock,
  HardDrive,
  CheckCircle2,
  AlertCircle,
  KeyRound,
  Server,
} from "lucide-react";

export default function SettingsPage() {
  const { user, loading: authLoading, refreshUser } = useAuth();
  const router = useRouter();

  const [stats, setStats] = useState<UserStats | null>(null);
  const [fullName, setFullName] = useState("");
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState<string | null>(null);

  // Password state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordSaving, setPasswordSaving] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/login");
    } else if (user) {
      setFullName(user.full_name || "");
      api.users.getStats().then(setStats).catch(console.error);
    }
  }, [user, authLoading, router]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileSaving(true);
    setProfileMessage(null);
    try {
      await api.users.updateProfile({ full_name: fullName.trim() || undefined });
      await refreshUser();
      setProfileMessage("Profile updated successfully");
    } catch (err: any) {
      setProfileMessage(err.message || "Failed to update profile");
    } finally {
      setProfileSaving(false);
    }
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMessage(null);

    if (newPassword !== confirmPassword) {
      setPasswordMessage({ type: "error", text: "New passwords do not match" });
      return;
    }

    if (newPassword.length < 8) {
      setPasswordMessage({ type: "error", text: "Password must be at least 8 characters" });
      return;
    }

    setPasswordSaving(true);
    try {
      await api.users.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordMessage({ type: "success", text: "Master password changed successfully" });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setPasswordMessage({ type: "error", text: err.message || "Failed to change password" });
    } finally {
      setPasswordSaving(false);
    }
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#070a12] text-cyan-400">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#070a12] text-slate-100 flex flex-col">
      <Header storageMb={stats?.storage_used_mb || 0} />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 py-10 space-y-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Settings
          </h1>
        </div>

        {/* Storage Metrics Panel */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
            <span className="text-xs text-slate-400 flex items-center gap-1.5 mb-2">
              <HardDrive className="w-4 h-4 text-cyan-400" />
              Storage Consumed
            </span>
            <p className="text-2xl font-bold text-white">
              {stats?.storage_used_mb.toFixed(2) || 0} MB
            </p>
            <p className="text-[11px] text-slate-500 mt-1">Local persistent volume</p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
            <span className="text-xs text-slate-400 flex items-center gap-1.5 mb-2">
              <KeyRound className="w-4 h-4 text-indigo-400" />
              Total Encrypted Images
            </span>
            <p className="text-2xl font-bold text-white">{stats?.total_images || 0}</p>
            <p className="text-[11px] text-slate-500 mt-1">Isolated server files</p>
          </div>

          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800">
            <span className="text-xs text-slate-400 flex items-center gap-1.5 mb-2">
              <Server className="w-4 h-4 text-emerald-400" />
              Active Albums
            </span>
            <p className="text-2xl font-bold text-white">{stats?.total_albums || 0}</p>
            <p className="text-[11px] text-slate-500 mt-1">Structured collections</p>
          </div>
        </div>

        {/* Profile Settings */}
        <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800">
          <h3 className="text-base font-semibold text-slate-200 mb-1 flex items-center gap-2">
            <UserIcon className="w-4 h-4 text-cyan-400" />
            Profile Details
          </h3>
          <p className="text-xs text-slate-400 mb-5">
            Your unique identity in the Vault cluster.
          </p>

          {profileMessage && (
            <div className="mb-4 p-3 rounded-xl bg-cyan-950/40 border border-cyan-800/60 text-xs text-cyan-300">
              {profileMessage}
            </div>
          )}

          <form onSubmit={handleUpdateProfile} className="space-y-4 max-w-lg">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Account ID (UUID)
              </label>
              <input
                type="text"
                disabled
                value={user.id}
                className="w-full bg-slate-950/80 border border-slate-800/80 rounded-xl px-3.5 py-2 text-xs font-mono text-slate-400 cursor-not-allowed"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">
                Email Address
              </label>
              <input
                type="email"
                disabled
                value={user.email}
                className="w-full bg-slate-950/80 border border-slate-800/80 rounded-xl px-3.5 py-2 text-xs text-slate-400 cursor-not-allowed"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-500 transition"
              />
            </div>

            <button
              type="submit"
              disabled={profileSaving}
              className="px-5 py-2 text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl shadow-lg shadow-cyan-600/20 disabled:opacity-50 transition"
            >
              {profileSaving ? "Saving..." : "Save Profile"}
            </button>
          </form>
        </div>

        {/* Change Password */}
        <div className="p-6 rounded-3xl bg-slate-900/60 border border-slate-800">
          <h3 className="text-base font-semibold text-slate-200 mb-1 flex items-center gap-2">
            <Lock className="w-4 h-4 text-indigo-400" />
            Update Password
          </h3>
          <p className="text-xs text-slate-400 mb-5">
            Passwords are encrypted using the Argon2id memory-hard algorithm.
          </p>

          {passwordMessage && (
            <div
              className={`mb-4 p-3 rounded-xl border text-xs flex items-center gap-2 ${
                passwordMessage.type === "success"
                  ? "bg-emerald-950/40 border-emerald-800/60 text-emerald-300"
                  : "bg-rose-950/40 border-rose-800/60 text-rose-300"
              }`}
            >
              {passwordMessage.type === "success" ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-400" />
              )}
              <span>{passwordMessage.text}</span>
            </div>
          )}

          <form onSubmit={handleUpdatePassword} className="space-y-4 max-w-lg">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Current Password
              </label>
              <input
                type="password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                New Password
              </label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-500 transition"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">
                Confirm New Password
              </label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-500 transition"
              />
            </div>

            <button
              type="submit"
              disabled={passwordSaving}
              className="px-5 py-2 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow-lg shadow-indigo-600/20 disabled:opacity-50 transition"
            >
              {passwordSaving ? "Updating..." : "Update Password"}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

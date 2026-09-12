"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import {
  Shield,
  UploadCloud,
  FolderLock,
  Settings as SettingsIcon,
  LogOut,
  Search,
  HardDrive,
  User as UserIcon,
} from "lucide-react";

interface HeaderProps {
  onOpenUpload?: () => void;
  onSearch?: (query: string) => void;
  storageMb?: number;
}

export default function Header({
  onOpenUpload,
  onSearch,
  storageMb = 0,
}: HeaderProps) {
  const { user, logout } = useAuth();
  const pathname = usePathname();
  const [searchQuery, setSearchQuery] = useState("");

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSearch) onSearch(searchQuery);
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-slate-800/80 bg-[#0b0f19]/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Logo & Brand */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 p-0.5 shadow-lg shadow-cyan-500/20 group-hover:shadow-cyan-500/40 transition">
              <div className="w-full h-full bg-[#070a12] rounded-[10px] flex items-center justify-center">
                <Shield className="w-5 h-5 text-cyan-400" />
              </div>
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-cyan-400 bg-clip-text text-transparent">
                VAULT
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 text-sm font-medium">
            <Link
              href="/"
              className={`px-3 py-1.5 rounded-lg transition ${
                pathname === "/"
                  ? "bg-slate-800/80 text-cyan-400 font-semibold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              Gallery
            </Link>
            <Link
              href="/albums"
              className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                pathname.startsWith("/albums")
                  ? "bg-slate-800/80 text-cyan-400 font-semibold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <FolderLock className="w-4 h-4" />
              Albums
            </Link>
            <Link
              href="/settings"
              className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                pathname === "/settings"
                  ? "bg-slate-800/80 text-cyan-400 font-semibold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40"
              }`}
            >
              <SettingsIcon className="w-4 h-4" />
              Settings
            </Link>
          </nav>
        </div>

        {/* Search Bar */}
        {onSearch && (
          <div className="flex-1 max-w-sm hidden sm:block">
            <form onSubmit={handleSearchSubmit} className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  onSearch(e.target.value);
                }}
                className="w-full bg-slate-900/80 border border-slate-800 rounded-xl pl-9 pr-4 py-1.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/80 focus:ring-1 focus:ring-cyan-500/50 transition"
              />
            </form>
          </div>
        )}

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          {/* Upload Button */}
          {onOpenUpload && (
            <button
              onClick={onOpenUpload}
              className="flex items-center gap-2 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white text-sm font-semibold px-3.5 py-1.5 rounded-xl shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40 transition active:scale-95"
            >
              <UploadCloud className="w-4 h-4" />
              <span className="hidden sm:inline">Upload</span>
            </button>
          )}

          {/* User Profile & Logout */}
          <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
            <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-xs font-semibold text-cyan-300 border border-slate-700">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : user?.email.charAt(0).toUpperCase()}
            </div>
            <button
              onClick={logout}
              title="Secure Logout"
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800/60 rounded-lg transition"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}

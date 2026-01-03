"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Youtube, Facebook, ScanFace, BarChart3, Sparkles, Globe, ChevronRight } from "lucide-react";

// Animated floating orb component
function FloatingOrb({ className, delay = 0 }: { className?: string; delay?: number }) {
  return (
    <div
      className={`absolute rounded-full blur-3xl animate-float opacity-30 ${className}`}
      style={{ animationDelay: `${delay}s` }}
    />
  );
}

// Particle effect component
function Particles() {
  const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number; size: number; duration: number }>>([]);

  useEffect(() => {
    const newParticles = Array.from({ length: 50 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 3 + 1,
      duration: Math.random() * 20 + 10,
    }));
    setParticles(newParticles);
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((particle) => (
        <div
          key={particle.id}
          className="absolute rounded-full bg-accent/30 animate-pulse"
          style={{
            left: `${particle.x}%`,
            top: `${particle.y}%`,
            width: `${particle.size}px`,
            height: `${particle.size}px`,
            animationDuration: `${particle.duration}s`,
          }}
        />
      ))}
    </div>
  );
}

// Feature card component
function FeatureCard({
  icon,
  title,
  description,
  gradient,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  gradient: string;
}) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 transition-all duration-300 hover:border-accent/50 hover:bg-white/10 hover:shadow-2xl hover:shadow-accent/20 hover:-translate-y-1">
      {/* Glow effect on hover */}
      <div className={`absolute -inset-px rounded-2xl bg-gradient-to-r ${gradient} opacity-0 group-hover:opacity-20 transition-opacity blur-xl`} />

      {/* Icon */}
      <div className={`relative mb-4 inline-flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br ${gradient}`}>
        {icon}
      </div>

      {/* Content */}
      <h3 className="relative mb-2 text-xl font-semibold text-white">{title}</h3>
      <p className="relative text-slate-400">{description}</p>
    </div>
  );
}

export default function LandingPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#0a0f1a]">
      {/* Animated gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0a0f1a] via-[#0f1729] to-[#1a0f29] animate-gradient" />

      {/* Floating orbs */}
      <FloatingOrb className="h-[500px] w-[500px] bg-purple-600 -top-48 -left-48" delay={0} />
      <FloatingOrb className="h-[400px] w-[400px] bg-cyan-500 top-1/3 right-0" delay={2} />
      <FloatingOrb className="h-[300px] w-[300px] bg-pink-500 bottom-0 left-1/4" delay={4} />
      <FloatingOrb className="h-[350px] w-[350px] bg-blue-500 bottom-1/4 right-1/4" delay={1} />

      {/* Particle effect */}
      <Particles />

      {/* Grid overlay */}
      <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-5" />

      {/* Content */}
      <div className="relative z-10 flex min-h-screen flex-col">
        {/* Header */}
        <header className="flex items-center justify-between p-6 lg:px-12">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-accent to-purple-600">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">Ministry Analytics</span>
          </div>

          <Link
            href="/dashboard"
            className="group flex items-center gap-2 rounded-full border border-white/20 bg-white/5 px-4 py-2 text-sm font-medium text-white backdrop-blur-sm transition-all hover:border-accent/50 hover:bg-white/10"
          >
            View Dashboard
            <ChevronRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
        </header>

        {/* Hero Section */}
        <main className="flex flex-1 flex-col items-center justify-center px-6 py-12 text-center">
          {/* Badge */}
          <div
            className={`mb-8 inline-flex items-center gap-2 rounded-full border border-accent/30 bg-accent/10 px-4 py-1.5 text-sm text-accent transition-all duration-700 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
          >
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
            </span>
            AI-Powered Sermon Discovery
          </div>

          {/* Main title with animated gradient */}
          <h1
            className={`mb-6 bg-gradient-to-r from-white via-cyan-200 to-purple-200 bg-clip-text text-5xl font-bold text-transparent sm:text-6xl lg:text-7xl transition-all duration-700 delay-100 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
          >
            Ministry Analytics
            <br />
            <span className="bg-gradient-to-r from-accent via-cyan-400 to-purple-400 bg-clip-text">
              Platform
            </span>
          </h1>

          {/* Subtitle with typewriter-like animation */}
          <p
            className={`mb-10 max-w-2xl text-lg text-slate-400 sm:text-xl transition-all duration-700 delay-200 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
          >
            Track, analyze, and forecast preaching ministry across YouTube and Facebook
            using advanced AI face recognition and intelligent content classification.
          </p>

          {/* CTA Buttons */}
          <div
            className={`flex flex-col gap-4 sm:flex-row transition-all duration-700 delay-300 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-4"}`}
          >
            <Link
              href="/setup"
              className="group relative inline-flex items-center justify-center gap-2 overflow-hidden rounded-full bg-gradient-to-r from-accent to-purple-600 px-8 py-4 text-lg font-semibold text-white shadow-lg shadow-accent/25 transition-all hover:shadow-xl hover:shadow-accent/40 hover:scale-105"
            >
              {/* Animated shine effect */}
              <div className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent group-hover:translate-x-full transition-transform duration-1000" />
              Get Started
              <ArrowRight className="h-5 w-5 transition-transform group-hover:translate-x-1" />
            </Link>

            <Link
              href="/dashboard"
              className="group inline-flex items-center justify-center gap-2 rounded-full border border-white/20 bg-white/5 px-8 py-4 text-lg font-medium text-white backdrop-blur-sm transition-all hover:border-accent/50 hover:bg-white/10"
            >
              <BarChart3 className="h-5 w-5" />
              View Analytics
            </Link>
          </div>
        </main>

        {/* Features Section */}
        <section className="px-6 pb-20 lg:px-12">
          <div className="mx-auto max-w-6xl">
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              <FeatureCard
                icon={<Youtube className="h-7 w-7 text-white" />}
                title="Multi-Platform Fetching"
                description="Automatically discover and fetch sermons from YouTube channels and Facebook pages worldwide."
                gradient="from-red-500 to-orange-500"
              />

              <FeatureCard
                icon={<ScanFace className="h-7 w-7 text-white" />}
                title="AI Face Recognition"
                description="Verify preachers in videos using advanced face recognition with DeepFace technology."
                gradient="from-accent to-cyan-500"
              />

              <FeatureCard
                icon={<BarChart3 className="h-7 w-7 text-white" />}
                title="Analytics & Forecasting"
                description="Powerful analytics dashboard with ML-powered forecasting for ministry planning."
                gradient="from-purple-500 to-pink-500"
              />
            </div>
          </div>
        </section>

        {/* Platform indicators */}
        <div className="flex justify-center gap-8 pb-8">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Youtube className="h-5 w-5 text-red-500" />
            YouTube
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Facebook className="h-5 w-5 text-blue-500" />
            Facebook
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Globe className="h-5 w-5 text-green-500" />
            Global Reach
          </div>
        </div>
      </div>

      {/* Custom styles for animations */}
      <style jsx>{`
        @keyframes float {
          0%, 100% {
            transform: translateY(0) rotate(0deg);
          }
          50% {
            transform: translateY(-30px) rotate(5deg);
          }
        }

        @keyframes gradient {
          0%, 100% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
        }

        .animate-float {
          animation: float 15s ease-in-out infinite;
        }

        .animate-gradient {
          background-size: 400% 400%;
          animation: gradient 15s ease infinite;
        }
      `}</style>
    </div>
  );
}

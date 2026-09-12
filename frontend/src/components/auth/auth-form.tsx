"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FileText, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { login, signup } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";

interface AuthFormProps {
  mode: "login" | "register";
}

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isRegister = mode === "register";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = isRegister
        ? await signup(email, fullName, password)
        : await login(email, password);

      setAuth(response.user, response.access_token);
      router.push("/chat");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-gradient-to-br from-accent/20 via-surface to-surface">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,_var(--tw-gradient-stops))] from-accent/30 via-transparent to-transparent" />
        <div className="relative z-10 flex flex-col justify-center px-16">
          <div className="mb-8 flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-accent/20 border border-accent/30">
              <FileText className="h-6 w-6 text-accent" />
            </div>
            <span className="text-2xl font-bold">BRD Agent</span>
          </div>
          <h1 className="text-4xl font-bold leading-tight mb-4">
            Agentic AI for
            <br />
            <span className="gradient-text">Requirements Engineering</span>
          </h1>
          <p className="text-gray-400 text-lg max-w-md leading-relaxed">
            Upload documents, describe your needs in natural language, and let
            AI generate comprehensive Business Requirements Documents.
          </p>
          <div className="mt-10 flex flex-col gap-4">
            {[
              "Upload any file format — PDF, DOCX, images",
              "Chat naturally like ChatGPT or Claude",
              "AI-powered BRD generation with guardrails",
            ].map((feature) => (
              <div key={feature} className="flex items-center gap-3 text-gray-300">
                <Sparkles className="h-4 w-4 text-accent shrink-0" />
                <span className="text-sm">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex w-full lg:w-1/2 items-center justify-center p-8">
        <div className="w-full max-w-md animate-slide-up">
          <div className="mb-8 lg:hidden flex items-center gap-3 justify-center">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/20">
              <FileText className="h-5 w-5 text-accent" />
            </div>
            <span className="text-xl font-bold">BRD Agent</span>
          </div>

          <h2 className="text-2xl font-bold mb-1">
            {isRegister ? "Create your account" : "Welcome back"}
          </h2>
          <p className="text-gray-400 mb-8">
            {isRegister
              ? "Start generating BRDs with AI assistance"
              : "Sign in to continue to your workspace"}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <Input
                id="fullName"
                label="Full name"
                placeholder="Jane Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            )}
            <Input
              id="email"
              label="Email"
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              id="password"
              label="Password"
              type="password"
              placeholder={isRegister ? "Min. 8 characters" : "Enter your password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={isRegister ? 8 : 1}
            />

            {error && (
              <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" size="lg" loading={loading}>
              {isRegister ? "Create account" : "Sign in"}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-400">
            {isRegister ? "Already have an account?" : "Don't have an account?"}{" "}
            <Link
              href={isRegister ? "/login" : "/register"}
              className="text-accent hover:text-accent-hover font-medium transition-colors"
            >
              {isRegister ? "Sign in" : "Create one"}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

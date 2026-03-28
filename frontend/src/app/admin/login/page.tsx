'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, LockKeyhole, ShieldCheck } from 'lucide-react';
import { useAdminAuth } from '@/contexts/AdminAuthContext';

export default function AdminLoginPage() {
  const router = useRouter();
  const { login, user, isLoading } = useAdminAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isLoading && user) {
      router.replace('/admin');
    }
  }, [isLoading, router, user]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      await login(email, password);
      router.replace('/admin');
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : 'Unable to sign in right now.',
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top_left,_rgba(0,206,209,0.18),_transparent_28%),radial-gradient(circle_at_bottom_right,_rgba(252,209,22,0.14),_transparent_24%),linear-gradient(180deg,#f7fbfc_0%,#eef6f7_55%,#f8f4ec_100%)] px-4 py-10">
      <div className="grid w-full max-w-6xl gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="rounded-[40px] border border-[#0A2342]/8 bg-[linear-gradient(145deg,#0f2e4f_0%,#154c79_38%,#00aeb0_100%)] p-8 text-white shadow-[0_32px_90px_rgba(10,35,66,0.18)] sm:p-12">
          <span className="inline-flex rounded-full border border-white/18 bg-white/10 px-4 py-2 text-xs uppercase tracking-[0.26em] text-white/78">
            Civic data workspace
          </span>
          <h1 className="mt-6 max-w-2xl text-4xl font-semibold leading-tight sm:text-5xl">
            Review, organize, and publish public-interest documents with confidence.
          </h1>
          <p className="mt-6 max-w-xl text-base leading-7 text-white/76 sm:text-lg">
            The admin experience follows the same visual language as the public product, with
            collections, record types, and structured review flows built for civic data teams.
          </p>

          <div className="mt-10 grid gap-4 sm:grid-cols-2">
            <div className="rounded-[28px] border border-white/14 bg-white/10 p-5 backdrop-blur">
              <ShieldCheck className="h-6 w-6 text-[#FCD116]" />
              <p className="mt-4 text-lg font-semibold">Protected ingestion</p>
              <p className="mt-2 text-sm leading-6 text-white/70">
                Admin auth gates uploads, processing, and ingestion runs with a real audit trail.
              </p>
            </div>
            <div className="rounded-[28px] border border-white/14 bg-white/10 p-5 backdrop-blur">
              <LockKeyhole className="h-6 w-6 text-[#8FF5F2]" />
              <p className="mt-4 text-lg font-semibold">Structured by design</p>
              <p className="mt-2 text-sm leading-6 text-white/70">
                Parser output, Gemini normalization, and metadata all target the same documented format.
              </p>
            </div>
          </div>
        </section>

        <section className="rounded-[40px] border border-[#0A2342]/8 bg-white/95 p-8 shadow-[0_28px_80px_rgba(10,35,66,0.08)] backdrop-blur sm:p-10">
          <div className="max-w-sm">
            <p className="text-sm uppercase tracking-[0.28em] text-[#0A2342]/45">Admin login</p>
            <h2 className="mt-3 text-3xl font-semibold text-[#0A2342]">Welcome back</h2>
            <p className="mt-3 text-sm leading-6 text-[#0A2342]/60">
              Sign in with your admin account to manage uploads and trigger document processing.
            </p>
          </div>

          <form className="mt-10 space-y-5" onSubmit={handleSubmit}>
            <label className="block">
              <span className="mb-2 block text-sm font-medium text-[#0A2342]/72">Email</span>
              <input
                type="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-[#0A2342] outline-none ring-0 placeholder:text-[#0A2342]/30 focus:border-[#00CED1]/45"
                placeholder="admin@bahamasopendata.com"
              />
            </label>

            <label className="block">
              <span className="mb-2 block text-sm font-medium text-[#0A2342]/72">Password</span>
              <input
                type="password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-2xl border border-[#0A2342]/10 bg-[#f8fcfc] px-4 py-3 text-[#0A2342] outline-none ring-0 placeholder:text-[#0A2342]/30 focus:border-[#00CED1]/45"
                placeholder="Enter your password"
              />
            </label>

            {error ? (
              <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {error}
              </div>
            ) : null}

            <button
              type="submit"
              disabled={submitting}
              className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-[#00CED1] px-5 py-3 text-sm font-semibold text-white shadow-[0_12px_30px_rgba(0,206,209,0.22)] hover:bg-[#00b8bb] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting ? 'Signing in…' : 'Enter admin panel'}
              <ArrowRight className="h-4 w-4" />
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}

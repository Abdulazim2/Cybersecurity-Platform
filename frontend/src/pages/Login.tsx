
import { useState } from 'react';
import { ShieldCheck, LockKeyhole, Mail, Eye, EyeOff, Loader2 } from 'lucide-react';
import api from '../services/api';

interface LoginProps {
  onLoginSuccess: () => void;
}

function Login({ onLoginSuccess }: LoginProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await api.post('/auth/login', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      sessionStorage.setItem('access_token', response.data.access_token);

      await api.get('/auth/me');

      onLoginSuccess();
    } catch (err: any) {
      sessionStorage.removeItem('access_token');

      if (err.response?.status === 401) {
        setError('Incorrect email/username or password.');
      } else if (err.response?.status === 403) {
        setError('Your account is inactive. Contact the administrator.');
      } else {
        setError('Unable to connect to the server. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F4F6F8] px-4 py-10">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-xl border border-[#E5E9ED] bg-white shadow-sm md:grid-cols-2">

        <div className="hidden flex-col justify-between bg-[#203D50] p-10 text-white md:flex">
          <div>
            <div className="mb-8 flex h-12 w-12 items-center justify-center rounded-lg bg-white/10">
              <ShieldCheck size={28} />
            </div>

            <h1 className="text-2xl font-semibold leading-relaxed">
              Industrial Security Platform
            </h1>

            <p className="mt-4 text-sm leading-7 text-white/70">
              AI-powered cybersecurity monitoring for industrial infrastructure.
              Monitor network activity, manage datasets, and analyze security predictions.
            </p>
          </div>

          <p className="text-xs text-white/50">
            Industrial Cybersecurity Monitoring · 2026
          </p>
        </div>

        <div className="flex flex-col justify-center p-7 sm:p-12">
          <div className="mb-8">
            <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-lg bg-[#EAF0F4] text-[#24485F] md:hidden">
              <ShieldCheck size={25} />
            </div>

            <p className="text-xs font-semibold tracking-widest text-[#648092]">
              SECURE ACCESS
            </p>

            <h2 className="mt-3 text-2xl font-semibold text-[#202B36]">
              Welcome back
            </h2>

            <p className="mt-2 text-sm text-[#89949E]">
              Sign in to access your security workspace.
            </p>
          </div>

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="mb-2 block text-sm font-medium text-[#52616D]">
                Email or Username
              </label>

              <div className="flex items-center rounded-md border border-[#DDE3E8] px-3 focus-within:border-[#416F85]">
                <Mail size={17} className="text-[#89949E]" />

                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your email or username"
                  className="w-full bg-transparent px-3 py-3 text-sm outline-none"
                  required
                />
              </div>
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium text-[#52616D]">
                Password
              </label>

              <div className="flex items-center rounded-md border border-[#DDE3E8] px-3 focus-within:border-[#416F85]">
                <LockKeyhole size={17} className="text-[#89949E]" />

                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full bg-transparent px-3 py-3 text-sm outline-none"
                  required
                />

                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-[#89949E]"
                  aria-label="Toggle password visibility"
                >
                  {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-md bg-[#24485F] py-3 text-sm font-semibold text-white transition hover:bg-[#19394E] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading && <Loader2 size={17} className="animate-spin" />}
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <p className="mt-8 text-center text-xs text-[#9AA4AD]">
            Protected Industrial Security Workspace
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;

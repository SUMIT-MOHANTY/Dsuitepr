import { Link } from 'react-router-dom';
import { CheckSquare } from 'lucide-react';
import { LoginForm } from '../components/auth/LoginForm';
import { ROUTES } from '../utils/constants';

export function LoginPage() {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header with Logo Only */}
      <header className="w-full px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <Link 
            to={ROUTES.LOGIN} 
            className="inline-flex items-center gap-2 text-slate-900 dark:text-white hover:opacity-80 transition-opacity"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <CheckSquare className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">TaskFlow</span>
          </Link>
        </div>
      </header>

      {/* Main Content - Centered Auth Card */}
      <main className="flex-1 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          {/* Welcome Text */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
              Welcome Back
            </h1>
            <p className="text-slate-600 dark:text-slate-400">
              Sign in to manage your tasks
            </p>
          </div>

          {/* Login Card */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-xl border border-slate-200 dark:border-slate-700 p-8">
            <LoginForm />

            {/* Register Link */}
            <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-700 text-center">
              <p className="text-slate-600 dark:text-slate-400">
                Don't have an account?{' '}
                <Link
                  to={ROUTES.REGISTER}
                  className="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 font-medium transition-colors"
                >
                  Create account
                </Link>
              </p>
            </div>
          </div>

          {/* Footer */}
          <p className="text-center text-sm text-slate-500 dark:text-slate-400 mt-8">
            Secure, fast, and simple task management
          </p>
        </div>
      </main>
    </div>
  );
}

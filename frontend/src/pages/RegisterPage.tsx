import { Link } from 'react-router-dom';
import { CheckSquare } from 'lucide-react';
import { RegisterForm } from '../components/auth/RegisterForm';
import { ROUTES } from '../utils/constants';

export function RegisterPage() {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header with Logo Only */}
      <header className="w-full px-6 py-4">
        <div className="max-w-7xl mx-auto">
          <Link
            to={ROUTES.HOME}
            className="inline-flex items-center gap-2 text-slate-900 dark:text-white hover:opacity-80 transition-opacity"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg">
              <CheckSquare className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold">TaskFlow</span>
          </Link>
        </div>
      </header>

      {/* Main Content - Centered Auth Card */}
      <main className="flex-1 flex items-center justify-center px-4 py-8">
        <RegisterForm />
      </main>

      {/* Footer */}
      <footer className="w-full px-6 py-4">
        <div className="max-w-7xl mx-auto text-center">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            By registering, you agree to our{' '}
            <Link
              to="#"
              className="text-indigo-600 hover:text-indigo-500 transition-colors"
            >
              Terms of Service
            </Link>{' '}
            and{' '}
            <Link
              to="#"
              className="text-indigo-600 hover:text-indigo-500 transition-colors"
            >
              Privacy Policy
            </Link>
          </p>
        </div>
      </footer>
    </div>
  );
}

export default RegisterPage;

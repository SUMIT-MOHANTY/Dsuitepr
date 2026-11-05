import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Eye, EyeOff, LogIn } from 'lucide-react';
import { Input } from '../common/Input';
import { Button } from '../common/Button';
import { ErrorMessage } from '../common/ErrorMessage';
import { useAuthStore } from '../../stores/authStore';
import { ROUTES } from '../../utils/constants';

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, isLoading, error: authError, clearError } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: 'onChange',
  });

  // Watch fields for real-time validation feedback
  const watchedFields = watch();

  const onSubmit = async (data: LoginFormData) => {
    setSubmitError(null);
    clearError();

    try {
      await login(data);
      
      // Get redirect URL from query params or default to dashboard
      const redirectTo = searchParams.get('redirect') || ROUTES.DASHBOARD;
      navigate(redirectTo, { replace: true });
    } catch (error) {
      // Error is handled by the store and displayed below
      setSubmitError(error instanceof Error ? error.message : 'Login failed');
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Username Field */}
      <div className="space-y-2">
        <label
          htmlFor="username"
          className="block text-sm font-medium text-slate-700 dark:text-slate-300"
        >
          Username
        </label>
        <Input
          id="username"
          type="text"
          placeholder="Enter your username"
          autoComplete="username"
          disabled={isLoading}
          error={errors.username?.message}
          {...register('username')}
          className={`
            ${errors.username ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500' : ''}
            ${watchedFields.username && !errors.username ? 'border-emerald-500' : ''}
          `}
        />
        {errors.username && (
          <p className="text-sm text-rose-600 dark:text-rose-400">
            {errors.username.message}
          </p>
        )}
      </div>

      {/* Password Field */}
      <div className="space-y-2">
        <label
          htmlFor="password"
          className="block text-sm font-medium text-slate-700 dark:text-slate-300"
        >
          Password
        </label>
        <div className="relative">
          <Input
            id="password"
            type={showPassword ? 'text' : 'password'}
            placeholder="Enter your password"
            autoComplete="current-password"
            disabled={isLoading}
            error={errors.password?.message}
            {...register('password')}
            className={`
              pr-10
              ${errors.password ? 'border-rose-500 focus:border-rose-500 focus:ring-rose-500' : ''}
              ${watchedFields.password && !errors.password ? 'border-emerald-500' : ''}
            `}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
            tabIndex={-1}
          >
            {showPassword ? (
              <EyeOff className="w-5 h-5" />
            ) : (
              <Eye className="w-5 h-5" />
            )}
          </button>
        </div>
        {errors.password && (
          <p className="text-sm text-rose-600 dark:text-rose-400">
            {errors.password.message}
          </p>
        )}
      </div>

      {/* Error Messages */}
      {(authError || submitError) && (
        <ErrorMessage
          message={authError || submitError || 'An error occurred'}
          onDismiss={() => {
            setSubmitError(null);
            clearError();
          }}
        />
      )}

      {/* Submit Button */}
      <Button
        type="submit"
        variant="primary"
        size="lg"
        isLoading={isLoading}
        disabled={isLoading}
        className="w-full"
        leftIcon={<LogIn className="w-5 h-5" />}
      >
        {isLoading ? 'Signing in...' : 'Sign In'}
      </Button>

      {/* Demo Account Hint */}
      <div className="text-center text-sm text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/50 p-3 rounded-lg">
        <p className="font-medium text-slate-600 dark:text-slate-300">Demo Account</p>
        <p>Username: <span className="font-mono text-slate-700 dark:text-slate-200">demo</span></p>
        <p>Password: <span className="font-mono text-slate-700 dark:text-slate-200">Demo123!</span></p>
      </div>
    </form>
  );
}

import { LoaderCircle } from "lucide-react";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "../../utils/cn";

type ButtonVariant = "primary" | "secondary" | "danger" | "ghost";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  loading?: boolean;
  icon?: ReactNode;
}

const variants: Record<ButtonVariant, string> = {
  primary: "bg-sahaya-900 text-white hover:bg-sahaya-700",
  secondary: "border border-slate-200 bg-white text-sahaya-900 hover:border-teal-300 hover:bg-sahaya-50",
  danger: "border border-red-200 bg-red-50 text-red-700 hover:bg-red-100",
  ghost: "text-sahaya-700 hover:bg-sahaya-50",
};

export function Button({
  variant = "primary",
  loading = false,
  icon,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={cn(
        "inline-flex min-h-10 items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-extrabold transition focus:outline-none focus:ring-2 focus:ring-sahaya-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60",
        variants[variant],
        className,
      )}
    >
      {loading ? <LoaderCircle aria-hidden="true" className="animate-spin" size={16} /> : icon}
      {children}
    </button>
  );
}

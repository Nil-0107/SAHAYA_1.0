import {
  cloneElement,
  isValidElement,
  useId,
  type InputHTMLAttributes,
  type ReactElement,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";
import { cn } from "../../utils/cn";

const controlClass =
  "w-full rounded-[10px] border border-slate-300 bg-white px-3 py-[11px] text-sm font-normal text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-sahaya-500 focus:ring-2 focus:ring-teal-100 disabled:bg-slate-100";

interface FieldControlProps {
  id?: string;
  "aria-describedby"?: string;
  "aria-invalid"?: boolean;
}

export function FormField({
  label,
  hint,
  error,
  children,
}: {
  label: string;
  hint?: string;
  error?: string;
  children: ReactNode;
}) {
  const generatedId = useId();
  const hintId = hint ? `${generatedId}-hint` : undefined;
  const errorId = error ? `${generatedId}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;
  const child = isValidElement(children)
    ? (children as ReactElement<FieldControlProps>)
    : null;
  const control = child
    ? cloneElement(child, {
        id: child.props.id ?? generatedId,
        "aria-describedby": [child.props["aria-describedby"], describedBy].filter(Boolean).join(" ") || undefined,
        "aria-invalid": error ? true : child.props["aria-invalid"],
      })
    : children;
  const controlId = child?.props.id ?? generatedId;

  return (
    <div className="grid gap-1.5">
      <label htmlFor={controlId} className="text-xs font-extrabold text-slate-700">
        {label}
      </label>
      {control}
      {hint ? (
        <span id={hintId} className="text-[11px] font-medium leading-5 text-slate-500">
          {hint}
        </span>
      ) : null}
      {error ? (
        <span id={errorId} className="text-[11px] font-bold text-red-600">
          {error}
        </span>
      ) : null}
    </div>
  );
}

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={cn(controlClass, props.className)} />;
}

export function SelectInput(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={cn(controlClass, props.className)} />;
}

export function TextArea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={cn(controlClass, "min-h-32 resize-y", props.className)} />;
}

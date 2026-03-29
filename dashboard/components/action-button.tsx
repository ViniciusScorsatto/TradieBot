"use client";

import { useFormStatus } from "react-dom";

export function ActionButton({ label, disabled = false }: { label: string; disabled?: boolean }) {
  const { pending } = useFormStatus();
  const isDisabled = pending || disabled;

  return (
    <button className="button small-button" type="submit" disabled={isDisabled} aria-disabled={isDisabled}>
      {pending ? "Working..." : label}
    </button>
  );
}

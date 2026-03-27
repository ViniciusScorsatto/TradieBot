"use client";

import { useFormStatus } from "react-dom";

export function ActionButton({ label }: { label: string }) {
  const { pending } = useFormStatus();

  return (
    <button className="button small-button" type="submit" disabled={pending} aria-disabled={pending}>
      {pending ? "Working..." : label}
    </button>
  );
}

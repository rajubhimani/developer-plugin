import type { ButtonHTMLAttributes } from "react";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual weight of the button. */
  variant?: "primary" | "secondary";
}

/** A native button: keyboard and screen reader behaviour come for free. */
export function Button({ variant = "primary", type = "button", ...rest }: ButtonProps) {
  return <button type={type} data-variant={variant} {...rest} />;
}

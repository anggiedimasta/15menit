import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

declare const __APP_PACKAGE_VERSION__: string;

export const APP_VERSION = __APP_PACKAGE_VERSION__;

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

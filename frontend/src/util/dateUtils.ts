/**
 * Calculate time until a due date in days, hours, and minutes
 * @param dueDate - ISO 8601 date string
 * @returns Object containing days, hours, minutes, and isPast flag
 */

// This file contains utility functions for handling date and time calculations related to assignments
// such as calculating time until due dates and formatting date strings for display.
export function calculateTimeUntilDue(dueDate?: string): {
  days: number;
  hours: number;
  minutes: number;
  isPast: boolean;
  formatted: string;
} {
  if (!dueDate) {
    return { days: 0, hours: 0, minutes: 0, isPast: false, formatted: "No due date" };
  }

  const now = new Date();
  const due = new Date(dueDate);
  const diffMs = due.getTime() - now.getTime();
  const isPast = diffMs < 0;
  
  const absDiffMs = Math.abs(diffMs);
  
  // Calculate days, hours, and minutes
  const days = Math.floor(absDiffMs / (1000 * 60 * 60 * 24));
  const hours = Math.floor((absDiffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((absDiffMs % (1000 * 60 * 60)) / (1000 * 60));
  
  // Format the string
  let formatted = "";
  if (isPast) {
    formatted = "Past due";
  } else if (days > 0) {
    formatted = `${days}d ${hours}h ${minutes}m`;
  } else if (hours > 0) {
    formatted = `${hours}h ${minutes}m`;
  } else if (minutes > 0) {
    formatted = `${minutes}m`;
  } else {
    formatted = "Due now";
  }
  
  return { days, hours, minutes, isPast, formatted };
}

/**
 * Format a date string to a more readable format
 * @param dateString - ISO 8601 date string
 * @returns Formatted date string
 */
export function formatDateTime(dateString?: string): string {
  if (!dateString) return "Not set";
  
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * Check if date is in the past
 * @param dateString - ISO 8601 date string
 * @returns true if date is in the past
 */
export function isPastDue(dateString?: string): boolean {
  if (!dateString) return false;
  return new Date(dateString) < new Date();
}

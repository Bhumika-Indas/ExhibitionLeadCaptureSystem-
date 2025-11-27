// Authentication utilities

export interface Employee {
  employee_id: number;
  full_name: string;
}

export function getEmployee(): Employee | null {
  if (typeof window === 'undefined') return null;

  const employeeStr = localStorage.getItem('employee');
  if (!employeeStr) return null;

  try {
    return JSON.parse(employeeStr);
  } catch {
    return null;
  }
}

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('auth_token');
}

export function isAuthenticated(): boolean {
  // Check for employee data instead of token (backend doesn't use tokens in dev mode)
  return !!getEmployee();
}

export function requireAuth(): Employee {
  const employee = getEmployee();
  if (!employee) {
    if (typeof window !== 'undefined') {
      window.location.href = '/auth/login';
    }
    throw new Error('Not authenticated');
  }
  return employee;
}

export function logout(): void {
  if (typeof window === 'undefined') return;

  // Clear all auth data
  localStorage.removeItem('auth_token');
  localStorage.removeItem('employee');
  localStorage.removeItem('chatMessages');

  // Redirect to login
  window.location.href = '/auth/login';
}

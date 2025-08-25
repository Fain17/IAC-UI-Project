import { useState, useEffect, useCallback } from 'react';
import roleVerificationService from '../utils/roleVerificationService';

interface UseRoleVerificationReturn {
  role: string | null;
  permissions: {
    create: boolean;
    read: boolean;
    write: boolean;
    delete: boolean;
    execute: boolean;
    assign: boolean;
  } | null;
  isLoading: boolean;
  error: string | null;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
  refreshRole: () => Promise<void>;
}

/**
 * React hook for role verification with caching and error handling
 * Provides secure access to user roles and permissions
 */
export const useRoleVerification = (): UseRoleVerificationReturn => {
  const [role, setRole] = useState<string | null>(null);
  const [permissions, setPermissions] = useState<UseRoleVerificationReturn['permissions']>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load role verification on mount
  useEffect(() => {
    loadRoleVerification();
  }, []);

  const loadRoleVerification = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const verifiedRole = await roleVerificationService.verifyUserRole();
      
      if (verifiedRole) {
        setRole(verifiedRole.role);
        setPermissions(verifiedRole.permissions);
      } else {
        setError('Failed to verify user role');
      }
    } catch (err) {
      console.error('Error loading role verification:', err);
      setError('Error verifying user role');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const hasPermission = useCallback((permission: string): boolean => {
    if (!permissions) return false;
    return permissions[permission as keyof typeof permissions] || false;
  }, [permissions]);

  const hasRole = useCallback((roleName: string): boolean => {
    return role === roleName;
  }, [role]);

  const refreshRole = useCallback(async (): Promise<void> => {
    await loadRoleVerification();
  }, [loadRoleVerification]);

  return {
    role,
    permissions,
    isLoading,
    error,
    hasPermission,
    hasRole,
    refreshRole
  };
};

/**
 * Hook for checking specific permissions
 */
export const usePermission = (permission: string): boolean => {
  const { permissions } = useRoleVerification();
  return permissions?.[permission as keyof typeof permissions] || false;
};

/**
 * Hook for checking specific roles
 */
export const useRole = (roleName: string): boolean => {
  const { role } = useRoleVerification();
  return role === roleName;
}; 
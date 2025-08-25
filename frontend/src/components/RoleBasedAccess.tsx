import React from 'react';
import { useRoleVerification } from '../hooks/useRoleVerification';

interface RoleBasedAccessProps {
  children: React.ReactNode;
  requiredRole?: string;
  requiredPermission?: string;
  fallback?: React.ReactNode;
  showLoading?: boolean;
}

/**
 * Role-based access control component
 * Provides secure access control based on verified server-side roles and permissions
 */
const RoleBasedAccess: React.FC<RoleBasedAccessProps> = ({
  children,
  requiredRole,
  requiredPermission,
  fallback = null,
  showLoading = true
}) => {
  const { role, permissions, isLoading, error } = useRoleVerification();

  // Show loading state if requested and still loading
  if (isLoading && showLoading) {
    return <div className="role-access-loading">Verifying permissions...</div>;
  }

  // Show error state if role verification failed
  if (error) {
    return <div className="role-access-error">Access denied: {error}</div>;
  }

  // Check role requirement
  if (requiredRole && role !== requiredRole) {
    return <>{fallback}</>;
  }

  // Check permission requirement
  if (requiredPermission && permissions && !permissions[requiredPermission as keyof typeof permissions]) {
    return <>{fallback}</>;
  }

  // Access granted
  return <>{children}</>;
};

/**
 * Higher-order component for role-based access control
 */
export const withRoleAccess = <P extends object>(
  Component: React.ComponentType<P>,
  requiredRole?: string,
  requiredPermission?: string,
  fallback?: React.ReactNode
) => {
  const WrappedComponent: React.FC<P> = (props) => (
    <RoleBasedAccess
      requiredRole={requiredRole}
      requiredPermission={requiredPermission}
      fallback={fallback}
    >
      <Component {...props} />
    </RoleBasedAccess>
  );

  WrappedComponent.displayName = `withRoleAccess(${Component.displayName || Component.name})`;
  return WrappedComponent;
};

/**
 * Hook for conditional rendering based on roles/permissions
 */
export const useRoleAccess = () => {
  const { role, permissions, isLoading, error } = useRoleVerification();

  const canAccess = (requiredRole?: string, requiredPermission?: string): boolean => {
    if (isLoading || error) return false;
    
    if (requiredRole && role !== requiredRole) return false;
    if (requiredPermission && permissions && !permissions[requiredPermission as keyof typeof permissions]) return false;
    
    return true;
  };

  return {
    role,
    permissions,
    isLoading,
    error,
    canAccess
  };
};

export default RoleBasedAccess; 
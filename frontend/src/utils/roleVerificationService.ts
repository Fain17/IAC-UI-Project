import { getCurrentUserRole, UserRoleResponse } from '../api';
import tokenManager from './tokenManager';

interface VerifiedUserRole {
  userId: string;
  role: string;
  permissions: {
    create: boolean;
    read: boolean;
    write: boolean;
    delete: boolean;
    execute: boolean;
    assign: boolean;
  };
  lastVerified: number;
  isValid: boolean;
}

class RoleVerificationService {
  private verificationCache: Map<string, VerifiedUserRole> = new Map();
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5 minutes
  private readonly VERIFICATION_KEY = 'role_verification_cache';

  constructor() {
    this.loadCacheFromStorage();
  }

  /**
   * Verify user role from server and validate against local storage
   * This follows the principle of "trust but verify" with server-side validation
   */
  async verifyUserRole(): Promise<VerifiedUserRole | null> {
    try {
      // Get local user data for comparison
      const localUser = tokenManager.getUser();
      if (!localUser?.id) {
        console.warn('No local user data found');
        return null;
      }

      // Check cache first
      const cached = this.getCachedVerification(localUser.id);
      if (cached && this.isCacheValid(cached)) {
        console.log('Using cached role verification');
        return cached;
      }

      // Fetch fresh role data from server
      console.log('Fetching fresh role verification from server');
      const response = await getCurrentUserRole();
      
      if (!response.data.success) {
        console.error('Role verification failed:', response.data);
        return null;
      }

      const serverData = response.data;
      
      // Validate server response integrity
      if (!this.validateServerResponse(serverData)) {
        console.error('Invalid server response format');
        return null;
      }

      // Cross-validate with local storage data
      const validationResult = this.crossValidateRole(localUser, serverData);
      
      if (!validationResult.isValid) {
        console.warn('Role validation failed:', validationResult.reason);
        // Clear potentially compromised data
        this.clearCache();
        return null;
      }

      // Create verified role object
      const verifiedRole: VerifiedUserRole = {
        userId: serverData.user_id,
        role: serverData.user_role,
        permissions: serverData.permissions,
        lastVerified: Date.now(),
        isValid: true
      };

      // Cache the verified role
      this.cacheVerification(verifiedRole);
      
      console.log('Role verification successful:', verifiedRole);
      return verifiedRole;

    } catch (error) {
      console.error('Error during role verification:', error);
      return null;
    }
  }

  /**
   * Cross-validate server response with local storage data
   * This prevents token manipulation and ensures data consistency
   */
  private crossValidateRole(localUser: any, serverData: UserRoleResponse): { isValid: boolean; reason?: string } {
    // Validate user ID consistency
    if (localUser.id !== serverData.user_id) {
      return { isValid: false, reason: 'User ID mismatch' };
    }

    // Validate role format
    if (!serverData.user_role || typeof serverData.user_role !== 'string') {
      return { isValid: false, reason: 'Invalid role format' };
    }

    // Validate permissions structure
    if (!serverData.permissions || typeof serverData.permissions !== 'object') {
      return { isValid: false, reason: 'Invalid permissions format' };
    }

    // Validate required permission fields
    const requiredPermissions = ['create', 'read', 'write', 'delete', 'execute', 'assign'];
    for (const permission of requiredPermissions) {
      if (typeof serverData.permissions[permission as keyof typeof serverData.permissions] !== 'boolean') {
        return { isValid: false, reason: `Invalid permission format: ${permission}` };
      }
    }

    // Validate raw permission data
    if (!serverData.raw_permission_data || 
        !serverData.raw_permission_data.id || 
        !serverData.raw_permission_data.user_id || 
        !serverData.raw_permission_data.role) {
      return { isValid: false, reason: 'Invalid raw permission data' };
    }

    return { isValid: true };
  }

  /**
   * Validate server response format and integrity
   */
  private validateServerResponse(data: any): boolean {
    return (
      data &&
      typeof data === 'object' &&
      typeof data.success === 'boolean' &&
      typeof data.user_id === 'string' &&
      typeof data.user_role === 'string' &&
      data.permissions &&
      typeof data.permissions === 'object' &&
      data.raw_permission_data &&
      typeof data.raw_permission_data === 'object'
    );
  }

  /**
   * Check if user has specific permission
   */
  async hasPermission(permission: keyof VerifiedUserRole['permissions']): Promise<boolean> {
    const verifiedRole = await this.verifyUserRole();
    return verifiedRole?.permissions[permission] || false;
  }

  /**
   * Check if user has specific role
   */
  async hasRole(role: string): Promise<boolean> {
    const verifiedRole = await this.verifyUserRole();
    return verifiedRole?.role === role;
  }

  /**
   * Get current verified role (cached if valid)
   */
  async getCurrentRole(): Promise<string | null> {
    const verifiedRole = await this.verifyUserRole();
    return verifiedRole?.role || null;
  }

  /**
   * Get all current permissions (cached if valid)
   */
  async getCurrentPermissions(): Promise<VerifiedUserRole['permissions'] | null> {
    const verifiedRole = await this.verifyUserRole();
    return verifiedRole?.permissions || null;
  }

  /**
   * Force refresh role verification (bypass cache)
   */
  async forceRefreshRole(): Promise<VerifiedUserRole | null> {
    this.clearCache();
    return this.verifyUserRole();
  }

  /**
   * Cache management methods
   */
  private getCachedVerification(userId: string): VerifiedUserRole | null {
    return this.verificationCache.get(userId) || null;
  }

  private cacheVerification(verifiedRole: VerifiedUserRole): void {
    this.verificationCache.set(verifiedRole.userId, verifiedRole);
    this.saveCacheToStorage();
  }

  private isCacheValid(cached: VerifiedUserRole): boolean {
    return Date.now() - cached.lastVerified < this.CACHE_DURATION;
  }

  private clearCache(): void {
    this.verificationCache.clear();
    this.saveCacheToStorage();
  }

  private saveCacheToStorage(): void {
    try {
      const cacheData = Array.from(this.verificationCache.entries());
      localStorage.setItem(this.VERIFICATION_KEY, JSON.stringify(cacheData));
    } catch (error) {
      console.warn('Failed to save cache to storage:', error);
    }
  }

  private loadCacheFromStorage(): void {
    try {
      const cached = localStorage.getItem(this.VERIFICATION_KEY);
      if (cached) {
        const cacheData = JSON.parse(cached);
        this.verificationCache = new Map(cacheData);
      }
    } catch (error) {
      console.warn('Failed to load cache from storage:', error);
      this.verificationCache.clear();
    }
  }

  /**
   * Clear verification cache (useful for logout)
   */
  clearVerificationCache(): void {
    this.clearCache();
  }
}

// Export singleton instance
const roleVerificationService = new RoleVerificationService();
export default roleVerificationService; 
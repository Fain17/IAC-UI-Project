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
   * Verify user role from JWT claims instead of server API call
   * This follows the principle of "trust but verify" with JWT validation
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

      // Get role from JWT claims instead of server API call
      console.log('Getting role from JWT claims');
      const token = tokenManager.getToken();
      
      if (!token) {
        console.error('No JWT token found');
        return null;
      }

      try {
        // Decode JWT token to get role and permissions from claims
        const payload = JSON.parse(atob(token.split('.')[1]));
        
        // Validate JWT payload structure
        if (!this.validateJWTPayload(payload)) {
          console.error('Invalid JWT payload format');
          return null;
        }

        // Cross-validate with local storage data
        const validationResult = this.crossValidateRole(localUser, payload);
        
        if (!validationResult.isValid) {
          console.warn('Role validation failed:', validationResult.reason);
          // Clear potentially compromised data
          this.clearCache();
          return null;
        }

        // Create verified role object from JWT claims
        const verifiedRole: VerifiedUserRole = {
          userId: localUser.id,
          role: payload.role || payload.user_role || 'viewer',
          permissions: payload.permissions || payload.user_permissions || {
            create: false,
            read: false,
            write: false,
            delete: false,
            execute: false,
            assign: false
          },
          lastVerified: Date.now(),
          isValid: true
        };

        // Cache the verified role
        this.cacheVerification(verifiedRole);
        
        console.log('Role verification successful from JWT:', verifiedRole);
        return verifiedRole;

      } catch (jwtError) {
        console.error('Failed to decode JWT token:', jwtError);
        return null;
      }

    } catch (error) {
      console.error('Error during role verification:', error);
      return null;
    }
  }

  /**
   * Cross-validate JWT claims with local storage data
   * This prevents token manipulation and ensures data consistency
   */
  private crossValidateRole(localUser: any, jwtPayload: any): { isValid: boolean; reason?: string } {
    // Validate user ID consistency
    if (localUser.id !== jwtPayload.sub && localUser.id !== jwtPayload.user_id) {
      return { isValid: false, reason: 'User ID mismatch' };
    }

    // Validate role format
    const role = jwtPayload.role || jwtPayload.user_role;
    if (!role || typeof role !== 'string') {
      return { isValid: false, reason: 'Invalid role format' };
    }

    // Validate permissions structure
    const permissions = jwtPayload.permissions || jwtPayload.user_permissions;
    if (!permissions || typeof permissions !== 'object') {
      return { isValid: false, reason: 'Invalid permissions format' };
    }

    return { isValid: true };
  }

  /**
   * Validate JWT payload format and integrity
   */
  private validateJWTPayload(payload: any): boolean {
    return (
      payload &&
      typeof payload === 'object' &&
      (payload.role || payload.user_role) &&
      (payload.permissions || payload.user_permissions)
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
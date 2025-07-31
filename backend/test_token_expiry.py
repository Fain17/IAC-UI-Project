#!/usr/bin/env python3
"""
Test script for short token durations
Run this to test token expiration behavior
"""

import asyncio
import time
from datetime import datetime, timezone

async def test_token_expiry():
    """Test the short token durations."""
    print("🔧 Testing Short Token Durations")
    print("=" * 50)
    
    # Import after setting up the environment
    from app.auth.service import auth_service
    
    print(f"📊 Current Settings:")
    print(f"   Access Token: {auth_service.access_token_expire_minutes} minutes")
    print(f"   Refresh Token: {auth_service.refresh_token_expire_days} days ({auth_service.refresh_token_expire_days * 24 * 60:.1f} minutes)")
    print(f"   Cleanup Interval: 60 seconds")
    print()
    
    # Simulate user login
    user_data = {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "is_admin": True
    }
    
    print("🔐 Creating tokens...")
    tokens = await auth_service.login_user(user_data)
    
    print(f"✅ Access Token: {tokens['access_token'][:20]}...")
    print(f"✅ Refresh Token: {tokens['refresh_token'][:20]}...")
    print()
    
    # Test token verification
    print("🔍 Testing token verification...")
    payload = await auth_service.verify_token(tokens['access_token'])
    if payload:
        print("✅ Access token is valid")
    else:
        print("❌ Access token is invalid")
    
    print()
    print("⏰ Waiting for tokens to expire...")
    print("   Access token expires in 1 minute")
    print("   Refresh token expires in ~5 minutes")
    print("   Cleanup runs every 1 minute")
    print()
    print("💡 Test scenarios:")
    print("   1. Wait 1 minute - access token should expire")
    print("   2. Wait 5 minutes - refresh token should expire")
    print("   3. Check /auth/debug-sessions for cleanup")
    print("   4. Use /auth/cleanup-sessions for manual cleanup")

if __name__ == "__main__":
    asyncio.run(test_token_expiry()) 
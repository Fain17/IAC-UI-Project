#!/usr/bin/env python3
"""
Script to fix and clean up problematic sessions
Run this to clean up sessions with parsing errors
"""

import asyncio
from datetime import datetime, timezone

async def fix_sessions():
    """Fix problematic sessions in the database."""
    print("🔧 Fixing Problematic Sessions")
    print("=" * 50)
    
    # Import after setting up the environment
    from app.db.database import db_service
    from app.auth.service import auth_service
    
    # Initialize database
    await db_service.initialize()
    
    try:
        print("📊 Checking current sessions...")
        
        # Get all sessions
        result = await db_service.client.execute("SELECT id, user_id, session_token, expires_at FROM user_sessions")
        
        print(f"Found {len(result.rows)} total sessions")
        
        problematic_sessions = []
        valid_sessions = []
        
        for row in result.rows:
            session_id, user_id, session_token, expires_at_str = row
            
            try:
                # Test parsing
                if isinstance(expires_at_str, str):
                    if 'T' in expires_at_str:
                        expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                    else:
                        expires_at = datetime.strptime(expires_at_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                elif isinstance(expires_at_str, (int, float)):
                    # Handle timestamp as Unix timestamp
                    # Check if it's milliseconds (13 digits) or seconds (10 digits)
                    if expires_at_str > 1e12:  # Likely milliseconds
                        expires_at = datetime.fromtimestamp(expires_at_str / 1000, tz=timezone.utc)
                    else:  # Likely seconds
                        expires_at = datetime.fromtimestamp(expires_at_str, tz=timezone.utc)
                elif isinstance(expires_at_str, datetime):
                    expires_at = expires_at_str
                else:
                    problematic_sessions.append((session_id, f"Unknown type: {type(expires_at_str)}"))
                    continue
                
                # Check if expired
                current_time = datetime.now(timezone.utc)
                if current_time > expires_at:
                    problematic_sessions.append((session_id, "Expired"))
                else:
                    valid_sessions.append(session_id)
                    
            except Exception as e:
                problematic_sessions.append((session_id, f"Parse error: {e}"))
        
        print(f"✅ Valid sessions: {len(valid_sessions)}")
        print(f"❌ Problematic sessions: {len(problematic_sessions)}")
        
        if problematic_sessions:
            print("\n🗑️ Cleaning up problematic sessions...")
            for session_id, reason in problematic_sessions:
                print(f"   Deleting session {session_id}: {reason}")
                await db_service.client.execute(
                    "DELETE FROM user_sessions WHERE id = ?",
                    [session_id]
                )
            print(f"✅ Deleted {len(problematic_sessions)} problematic sessions")
        else:
            print("✅ No problematic sessions found")
        
        # Run cleanup
        print("\n🧹 Running cleanup...")
        cleaned_count = await auth_service.cleanup_expired_sessions()
        active_count = await auth_service.get_active_sessions_count()
        
        print(f"✅ Cleanup complete:")
        print(f"   Sessions cleaned: {cleaned_count}")
        print(f"   Active sessions remaining: {active_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await db_service.close()

if __name__ == "__main__":
    asyncio.run(fix_sessions()) 
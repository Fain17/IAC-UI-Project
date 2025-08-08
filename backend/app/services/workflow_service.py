from app.db.repositories import WorkflowRepository
from app.services.file_storage_service import file_storage
from typing import Dict, List, Optional
import logging
import json
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_workflow_id() -> str:
    """Generate a unique workflow ID."""
    return str(uuid.uuid4())

def generate_step_id() -> str:
    """Generate a unique step ID."""
    return f"step_{uuid.uuid4().hex[:8]}"

def create_step_directory_safe(workflow_id: str, step_id: str, step_name: str, step_order: int) -> Optional[str]:
    """
    Safely create a step directory and return the directory name.
    Returns None if creation fails.
    """
    try:
        step_dir = file_storage.create_step_directory(workflow_id, step_id, step_name, step_order)
        # Return the directory name (last part of the path)
        return step_dir.name
    except Exception as e:
        logger.error(f"Failed to create step directory for step {step_id}: {e}")
        return None

def validate_step_orders(steps: List[Dict]) -> Dict:
    """
    Validate that step orders are unique and sequential.
    Returns dict with success status and error message if validation fails.
    """
    if not steps:
        return {"success": True}
    
    # Check for duplicate orders
    orders = [step.get("order") for step in steps if step.get("order") is not None]
    if len(orders) != len(set(orders)):
        return {"success": False, "error": "Duplicate order numbers found. Each step must have a unique order."}
    
    # Check for gaps in ordering (optional - can be relaxed if needed)
    if orders:
        sorted_orders = sorted(orders)
        expected_orders = list(range(1, len(orders) + 1))
        if sorted_orders != expected_orders:
            return {"success": False, "error": "Step orders must be sequential starting from 1 without gaps."}
    
    return {"success": True}

def get_next_available_order(steps: List[Dict]) -> int:
    """Get the next available order number for a new step."""
    if not steps:
        return 1
    
    existing_orders = [step.get("order", 0) for step in steps if step.get("order") is not None]
    if not existing_orders:
        return 1
    
    return max(existing_orders) + 1

def reorder_steps_sequentially(steps: List[Dict]) -> List[Dict]:
    """
    Reorder steps to ensure sequential ordering (1, 2, 3, ...).
    Returns the reordered steps list.
    
    OPTIMIZATION NOTE: For large step lists (>100 steps), consider implementing:
    1. Linked list structure for O(1) reordering
    2. Skip list for O(log n) access by position
    3. B-tree for O(log n) operations
    
    Current implementation: O(n log n) due to sorting
    """
    if not steps:
        return steps
    
    # Sort steps by current order
    sorted_steps = sorted(steps, key=lambda x: x.get("order", 0))
    
    # Reassign orders sequentially
    for i, step in enumerate(sorted_steps, 1):
        step["order"] = i
        step["updated_at"] = datetime.now().isoformat()
    
    return sorted_steps

def optimize_reordering_for_large_lists(steps: List[Dict]) -> List[Dict]:
    """
    Optimized reordering for large step lists (>100 steps).
    This is a placeholder for future optimization.
    
    RECOMMENDED IMPLEMENTATION:
    1. Use a doubly-linked list structure
    2. Maintain a separate order index
    3. Implement skip list for fast access
    4. Use B-tree for complex reordering operations
    
    Example structure:
    {
        "steps": [
            {
                "id": "step_123",
                "name": "Step 1",
                "order": 1,
                "next_id": "step_456",
                "prev_id": null
            },
            {
                "id": "step_456", 
                "name": "Step 2",
                "order": 2,
                "next_id": "step_789",
                "prev_id": "step_123"
            }
        ],
        "order_index": {
            "1": "step_123",
            "2": "step_456", 
            "3": "step_789"
        }
    }
    """
    # For now, use the standard reordering
    return reorder_steps_sequentially(steps)

async def create_workflow(user_id: int, name: str, description: str = None, steps: List[Dict] = None) -> Dict:
    """
    Create a new workflow for a user.
    Returns dict with success status and workflow ID or error message.
    """
    try:
        if not name or not name.strip():
            return {"success": False, "error": "Workflow name is required"}
        
        # Generate workflow ID
        workflow_id = generate_workflow_id()
        
        # Process steps to add IDs if not present
        processed_steps = []
        if steps:
            for i, step in enumerate(steps):
                if not step.get("id"):
                    step["id"] = generate_step_id()
                if not step.get("order"):
                    step["order"] = i + 1
                step["created_at"] = datetime.now().isoformat()
                step["updated_at"] = datetime.now().isoformat()
                processed_steps.append(step)
            
            # Validate step orders
            validation = validate_step_orders(processed_steps)
            if not validation["success"]:
                return validation
        
        # Create workflow in database
        success = await WorkflowRepository.create(
            workflow_id=workflow_id,
            user_id=user_id,
            name=name.strip(),
            description=description.strip() if description else None,
            steps=processed_steps
        )
        
        if not success:
            return {"success": False, "error": "Failed to create workflow"}
        
        # Create workflow directory
        try:
            file_storage.create_workflow_directory(workflow_id)
        except Exception as dir_err:
            logger.error(f"Failed to create workflow directory for {workflow_id}: {dir_err}")
            # Rollback DB record if directory creation fails
            try:
                await WorkflowRepository.delete(workflow_id, user_id)
            except Exception as _:
                logger.error(f"Failed to rollback workflow {workflow_id} after directory creation error")
            return {"success": False, "error": "Failed to create workflow directory"}
        
        # Create step directories for initial steps
        if processed_steps:
            for step in processed_steps:
                step_dir_name = create_step_directory_safe(
                    workflow_id, 
                    step["id"], 
                    step["name"], 
                    step["order"]
                )
                if step_dir_name:
                    step["directory_name"] = step_dir_name
                else:
                    logger.warning(f"Failed to create directory for step {step['id']}, but continuing...")
        
        return {
            "success": True, 
            "workflow_id": workflow_id,
            "message": f"Workflow '{name}' created successfully"
        }
            
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        return {"success": False, "error": "Internal server error"}

async def get_user_workflows(user_id: int) -> List[Dict]:
    """
    Get all workflows for a specific user.
    Returns list of workflow dictionaries.
    """
    try:
        workflows = await WorkflowRepository.get_all_by_user(user_id)
        return workflows
    except Exception as e:
        logger.error(f"Error getting user workflows: {e}")
        return []

async def get_workflow_by_id(workflow_id: str, user_id: int) -> Optional[Dict]:
    """
    Get a specific workflow by ID for a user.
    Returns workflow dict or None if not found.
    """
    try:
        workflow = await WorkflowRepository.get_by_id(workflow_id, user_id)
        return workflow
    except Exception as e:
        logger.error(f"Error getting workflow by ID: {e}")
        return None

async def delete_workflow(workflow_id: str, user_id: int) -> Dict:
    """
    Delete a workflow by ID for a specific user.
    Returns dict with success status and message.
    """
    try:
        # First check if workflow exists and belongs to user
        workflow = await WorkflowRepository.get_by_id(workflow_id, user_id)
        if not workflow:
            return {"success": False, "error": "Workflow not found or access denied"}
        
        # Delete the workflow from database
        success = await WorkflowRepository.delete(workflow_id, user_id)
        
        if success:
            # Clean up workflow files directory
            try:
                await file_storage.cleanup_workflow_files(workflow_id, user_id)
            except Exception as file_err:
                logger.error(f"Failed to cleanup workflow files for {workflow_id}: {file_err}")
                # Continue even if file cleanup fails
            
            return {
                "success": True,
                "message": f"Workflow '{workflow['name']}' deleted successfully"
            }
        else:
            return {"success": False, "error": "Failed to delete workflow"}
            
    except Exception as e:
        logger.error(f"Error deleting workflow: {e}")
        return {"success": False, "error": "Internal server error"}

async def update_workflow(workflow_id: str, user_id: int, name: str = None, description: str = None, steps: List[Dict] = None, is_active: bool = None) -> Dict:
    """
    Update a workflow by ID for a specific user.
    Returns dict with success status and message.
    """
    try:
        # First check if workflow exists and belongs to user
        workflow = await WorkflowRepository.get_by_id(workflow_id, user_id)
        if not workflow:
            return {"success": False, "error": "Workflow not found or access denied"}
        
        # Update the workflow
        success = await WorkflowRepository.update(
            workflow_id=workflow_id,
            user_id=user_id,
            name=name,
            description=description,
            steps=steps,
            is_active=is_active
        )
        
        if success:
            return {
                "success": True,
                "message": f"Workflow '{workflow['name']}' updated successfully"
            }
        else:
            return {"success": False, "error": "Failed to update workflow"}
            
    except Exception as e:
        logger.error(f"Error updating workflow: {e}")
        return {"success": False, "error": "Internal server error"} 
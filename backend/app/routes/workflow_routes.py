from fastapi import APIRouter, Request, Depends, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from app.services.workflow_service import (
    create_workflow, get_user_workflows, get_workflow_by_id, 
    delete_workflow, update_workflow, validate_step_orders, 
    get_next_available_order, reorder_steps_sequentially, generate_step_id
)
from app.db.repositories import WorkflowRepository
from app.auth.dependencies import get_current_user
from app.db.models import WorkflowCreateRequest, WorkflowUpdate, WorkflowStep
from typing import List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow")

@router.post("/create", tags=["Workflow"])
async def create_workflow_route(
    workflow_data: WorkflowCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new workflow with name and description.
    
    This creates a workflow template with no steps initially.
    Steps can be added later using the append step route.
    
    Note: Steps are not included in the initial creation and will be an empty list.
    """
    try:
        if not workflow_data.name or not workflow_data.name.strip():
            raise HTTPException(status_code=400, detail="Workflow name is required")
        
        # Create workflow with empty steps list
        result = await create_workflow(
            user_id=current_user["id"],
            name=workflow_data.name.strip(),
            description=workflow_data.description.strip() if workflow_data.description else None,
            steps=[]  # Default to empty list
        )
        
        if result["success"]:
            return JSONResponse({
                "success": True,
                "workflow_id": result["workflow_id"],
                "message": result["message"],
                "steps_count": 0
            }, status_code=201)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/list", tags=["Workflow"])
async def list_workflows(current_user: dict = Depends(get_current_user)):
    """
    Get all workflows for the authenticated user.
    Returns a list of workflows with their details.
    """
    try:
        workflows = await get_user_workflows(current_user["id"])
        return JSONResponse({
            "success": True,
            "workflows": workflows,
            "count": len(workflows)
        })
    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{workflow_id}", tags=["Workflow"])
async def get_workflow_route(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific workflow by ID.
    Only returns workflows owned by the authenticated user.
    """
    try:
        workflow = await get_workflow_by_id(workflow_id, current_user["id"])
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found or access denied")
        
        return JSONResponse({
            "success": True,
            "workflow": workflow
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{workflow_id}", tags=["Workflow"])
async def delete_workflow_route(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a workflow by ID and all its associated files.
    Only allows deletion of workflows owned by the authenticated user.
    """
    try:
        result = await delete_workflow(workflow_id, current_user["id"])
        
        if result["success"]:
            return JSONResponse(result)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{workflow_id}", tags=["Workflow"])
async def update_workflow_route(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a workflow by ID.
    Only allows updates to workflows owned by the authenticated user.
    """
    try:
        # Convert Pydantic model to dict for service
        update_data = {}
        if workflow_data.name is not None:
            update_data["name"] = workflow_data.name
        if workflow_data.description is not None:
            update_data["description"] = workflow_data.description
        if workflow_data.steps is not None:
            # Convert WorkflowStep objects to dictionaries
            update_data["steps"] = [step.model_dump() for step in workflow_data.steps]
        if workflow_data.is_active is not None:
            update_data["is_active"] = workflow_data.is_active
        
        result = await update_workflow(
            workflow_id=workflow_id,
            user_id=current_user["id"],
            **update_data
        )
        
        if result["success"]:
            return JSONResponse(result)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ==================== STEP MANAGEMENT ROUTES ====================

@router.post("/{workflow_id}/steps", tags=["Workflow Steps"])
async def append_step_route(
    workflow_id: str,
    step_data: WorkflowStep,
    current_user: dict = Depends(get_current_user)
):
    """
    Append a new step to the end of a workflow.
    
    Request body should contain:
    {
        "name": "step_name",
        "description": "step_description", 
        "order": 1,
        "script_type": "python",
        "script_filename": "script.py",
        "run_command": "python script.py",
        "dependencies": ["boto3", "requests"],
        "parameters": {"ENV": "production"},
        "is_active": true
    }
    
    Note: The 'id' field is auto-generated as a UUID (e.g., step_a533e6a0) and should not be provided.
    Script types supported: "python", "nodejs"
    The order will be automatically set to the next available position if not provided.
    If order is provided, it must be unique and not conflict with existing steps.
    A step directory will be created under the workflow directory for this step.
    """
    try:
        # Get the current workflow
        workflow = await get_workflow_by_id(workflow_id, current_user["id"])
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found or access denied")
        
        # Get current steps
        current_steps = workflow.get("steps", [])
        
        # Validate step data
        if not step_data.name or not step_data.name.strip():
            raise HTTPException(status_code=400, detail="Step name is required")
        
        # Convert step to dict and always auto-generate UUID
        new_step = step_data.model_dump(exclude={'id'})  # Exclude any provided id
        
        # Always generate a new UUID for the step
        new_step["id"] = generate_step_id()
        
        # Handle order assignment
        if step_data.order is None:
            # Auto-assign order if not provided
            new_step["order"] = get_next_available_order(current_steps)
        else:
            # Check if the provided order conflicts with existing steps
            existing_orders = [step.get("order") for step in current_steps if step.get("order") is not None]
            if step_data.order in existing_orders:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Order {step_data.order} already exists. Please use a unique order number or let the system auto-assign one."
                )
        
        # Add timestamps
        new_step["created_at"] = datetime.now().isoformat()
        new_step["updated_at"] = datetime.now().isoformat()
        
        # Create step directory
        try:
            from app.services.workflow_service import create_step_directory_safe
            step_dir_name = create_step_directory_safe(
                workflow_id,
                new_step["id"],
                new_step["name"],
                new_step["order"]
            )
            if step_dir_name:
                new_step["directory_name"] = step_dir_name
                logger.info(f"Created step directory: {step_dir_name} for step {new_step['id']}")
            else:
                logger.warning(f"Failed to create directory for step {new_step['id']}, but continuing...")
        except Exception as dir_err:
            logger.error(f"Error creating step directory: {dir_err}")
            # Continue without directory creation - step will still be created
        
        # Add the new step
        current_steps.append(new_step)
        
        # Validate all step orders after adding the new step
        validation = validate_step_orders(current_steps)
        if not validation["success"]:
            raise HTTPException(status_code=400, detail=validation["error"])
        
        # Update the workflow with new steps
        result = await update_workflow(
            workflow_id=workflow_id,
            user_id=current_user["id"],
            steps=current_steps
        )
        
        if result["success"]:
            return JSONResponse({
                "success": True,
                "message": f"Step '{step_data.name}' added successfully",
                "step": new_step,
                "total_steps": len(current_steps)
            }, status_code=201)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error appending step: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{workflow_id}/steps/{step_order}", tags=["Workflow Steps"])
async def delete_step_route(
    workflow_id: str,
    step_order: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a specific step from the workflow by its order position.
    Step order is 1-based (1 = first step).
    After deletion, remaining steps will be reordered sequentially.
    The step directory will also be deleted.
    """
    try:
        # Get the current workflow
        workflow = await get_workflow_by_id(workflow_id, current_user["id"])
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found or access denied")
        
        # Get current steps
        current_steps = workflow.get("steps", [])
        
        # Validate step order
        if step_order < 1 or step_order > len(current_steps):
            raise HTTPException(status_code=404, detail=f"Step at position {step_order} not found")
        
        # Find and remove the step
        step_to_delete = None
        for i, step in enumerate(current_steps):
            if step["order"] == step_order:
                step_to_delete = step
                del current_steps[i]
                break
        
        if not step_to_delete:
            raise HTTPException(status_code=404, detail=f"Step at position {step_order} not found")
        
        # Delete step directory if it exists
        if step_to_delete.get("directory_name"):
            try:
                from app.services.file_storage_service import file_storage
                success = file_storage.delete_step_directory(workflow_id, step_to_delete["directory_name"])
                if success:
                    logger.info(f"Deleted step directory: {step_to_delete['directory_name']}")
                else:
                    logger.warning(f"Failed to delete step directory: {step_to_delete['directory_name']}")
            except Exception as dir_err:
                logger.error(f"Error deleting step directory: {dir_err}")
                # Continue with step deletion even if directory deletion fails
        
        # Reorder remaining steps sequentially
        current_steps = reorder_steps_sequentially(current_steps)
        
        # Validate step orders after reordering
        validation = validate_step_orders(current_steps)
        if not validation["success"]:
            raise HTTPException(status_code=400, detail=validation["error"])
        
        # Update the workflow with updated steps
        result = await update_workflow(
            workflow_id=workflow_id,
            user_id=current_user["id"],
            steps=current_steps
        )
        
        if result["success"]:
            return JSONResponse({
                "success": True,
                "message": f"Step '{step_to_delete['name']}' deleted successfully",
                "deleted_step": step_to_delete,
                "total_steps": len(current_steps)
            })
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting step: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{workflow_id}/steps/reorder", tags=["Workflow Steps"])
async def reorder_steps_route(
    workflow_id: str,
    step_orders: List[int] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Reorder multiple steps in the workflow efficiently.
    
    Request body should be a list of step orders in the desired sequence.
    Example: [3, 1, 2] would move step 3 to position 1, step 1 to position 2, etc.
    After reordering, steps will be assigned sequential order numbers (1, 2, 3, ...).
    
    This route is optimized for:
    - Bulk reordering of multiple steps
    - Drag-and-drop reordering in UI
    - Efficient step sequence changes
    
    For individual step updates, use the /{step_order} endpoint instead.
    """
    try:
        # Get the current workflow
        workflow = await get_workflow_by_id(workflow_id, current_user["id"])
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found or access denied")
        
        # Get current steps
        current_steps = workflow.get("steps", [])
        
        # Validate step orders
        if len(step_orders) != len(current_steps):
            raise HTTPException(status_code=400, detail=f"Expected {len(current_steps)} step orders, got {len(step_orders)}")
        
        # Validate that all step orders are valid
        valid_orders = [step["order"] for step in current_steps]
        for order in step_orders:
            if order not in valid_orders:
                raise HTTPException(status_code=400, detail=f"Invalid step order: {order}")
        
        # Check for duplicate orders in the request
        if len(step_orders) != len(set(step_orders)):
            raise HTTPException(status_code=400, detail="Duplicate step orders found in the reorder request")
        
        # Create a mapping of old order to step
        step_map = {step["order"]: step for step in current_steps}
        
        # Reorder steps
        reordered_steps = []
        for new_order, old_order in enumerate(step_orders, 1):
            step = step_map[old_order].copy()
            step["order"] = new_order
            step["updated_at"] = datetime.now().isoformat()
            reordered_steps.append(step)
        
        # Validate step orders after reordering
        validation = validate_step_orders(reordered_steps)
        if not validation["success"]:
            raise HTTPException(status_code=400, detail=validation["error"])
        
        # Update the workflow with reordered steps
        result = await update_workflow(
            workflow_id=workflow_id,
            user_id=current_user["id"],
            steps=reordered_steps
        )
        
        if result["success"]:
            return JSONResponse({
                "success": True,
                "message": "Steps reordered successfully",
                "steps": reordered_steps,
                "total_steps": len(reordered_steps)
            })
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reordering steps: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{workflow_id}/steps/{step_order}", tags=["Workflow Steps"])
async def update_step_route(
    workflow_id: str,
    step_order: int,
    step_data: WorkflowStep,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a specific step in the workflow by its order position.
    Step order is 1-based (1 = first step).
    If updating the order, the new order must be unique and not conflict with existing steps.
    
    This route is useful for:
    - Updating step properties (name, description, script_type, etc.)
    - Moving a single step to a different position
    - Individual step modifications
    
    Note: The 'id' field is auto-generated and cannot be updated.
    For bulk reordering of multiple steps, use the /reorder endpoint instead.
    """
    try:
        # Get the current workflow
        workflow = await get_workflow_by_id(workflow_id, current_user["id"])
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found or access denied")
        
        # Get current steps
        current_steps = workflow.get("steps", [])
        
        # Validate step order
        if step_order < 1 or step_order > len(current_steps):
            raise HTTPException(status_code=404, detail=f"Step at position {step_order} not found")
        
        # Find and update the step
        step_found = False
        for step in current_steps:
            if step["order"] == step_order:
                # Check if the new order conflicts with existing steps (if order is being updated)
                if step_data.order is not None and step_data.order != step_order:
                    existing_orders = [s.get("order") for s in current_steps if s.get("order") is not None and s != step]
                    if step_data.order in existing_orders:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Order {step_data.order} already exists. Please use a unique order number."
                        )
                
                # Update step data (exclude id field as it cannot be updated)
                update_data = step_data.model_dump(exclude_unset=True)
                step.update(update_data)
                step["updated_at"] = datetime.now().isoformat()
                step_found = True
                break
        
        if not step_found:
            raise HTTPException(status_code=404, detail=f"Step at position {step_order} not found")
        
        # Validate all step orders after update
        validation = validate_step_orders(current_steps)
        if not validation["success"]:
            raise HTTPException(status_code=400, detail=validation["error"])
        
        # Update the workflow with updated steps
        result = await update_workflow(
            workflow_id=workflow_id,
            user_id=current_user["id"],
            steps=current_steps
        )
        
        if result["success"]:
            return JSONResponse({
                "success": True,
                "message": f"Step updated successfully",
                "updated_step": step_data.model_dump(exclude_unset=True),
                "total_steps": len(current_steps)
            })
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating step: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{workflow_id}/steps", tags=["Workflow Steps"])
async def list_steps_route(
    workflow_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all steps for a specific workflow.
    """
    try:
        workflow = await get_workflow_by_id(workflow_id, current_user["id"])
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found or access denied")
        
        steps = workflow.get("steps", [])
        
        return JSONResponse({
            "success": True,
            "workflow_id": workflow_id,
            "workflow_name": workflow["name"],
            "steps": steps,
            "total_steps": len(steps)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing steps: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{workflow_id}/steps/id/{step_id}", tags=["Workflow Steps"])
async def update_step_by_id_route(
    workflow_id: str,
    step_id: str,
    step_data: WorkflowStep,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a specific step in the workflow by its step ID.
    Step ID is immutable and unique (e.g., step_a533e6a0).
    If updating the order, the new order must be unique and not conflict with existing steps.
    
    This route is useful for:
    - Updating step properties (name, description, script_type, etc.)
    - Moving a single step to a different position
    - Individual step modifications
    
    Note: The 'id' field is auto-generated and cannot be updated.
    For bulk reordering of multiple steps, use the /reorder endpoint instead.
    """
    try:
        # Get the current workflow
        workflow = await get_workflow_by_id(workflow_id, current_user["id"])
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found or access denied")
        
        # Get current steps
        current_steps = workflow.get("steps", [])
        
        # Find the step by ID
        step_found = False
        step_to_update = None
        for step in current_steps:
            if step["id"] == step_id:
                step_to_update = step
                step_found = True
                break
        
        if not step_found:
            raise HTTPException(status_code=404, detail=f"Step with ID {step_id} not found")
        
        # Check if the new order conflicts with existing steps (if order is being updated)
        if step_data.order is not None and step_data.order != step_to_update["order"]:
            existing_orders = [s.get("order") for s in current_steps if s.get("order") is not None and s["id"] != step_id]
            if step_data.order in existing_orders:
                raise HTTPException(
                    status_code=400,
                    detail=f"Order {step_data.order} already exists. Please use a unique order number."
                )
        
        # Update step data (exclude id field as it cannot be updated)
        update_data = step_data.model_dump(exclude_unset=True)
        step_to_update.update(update_data)
        step_to_update["updated_at"] = datetime.now().isoformat()
        
        # Validate all step orders after update
        validation = validate_step_orders(current_steps)
        if not validation["success"]:
            raise HTTPException(status_code=400, detail=validation["error"])
        
        # Update the workflow with updated steps
        result = await update_workflow(
            workflow_id=workflow_id,
            user_id=current_user["id"],
            steps=current_steps
        )
        
        if result["success"]:
            return JSONResponse({
                "success": True,
                "message": f"Step '{step_to_update['name']}' updated successfully",
                "updated_step": step_to_update,
                "total_steps": len(current_steps)
            })
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating step by ID: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 
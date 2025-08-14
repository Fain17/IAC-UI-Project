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
from app.services.execution_service import execution_service
from app.services.file_storage_service import file_storage

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
    Returns workflows owned by the user and workflows shared with teams the user is a member of.
    """
    try:
        # Get user's own workflows
        own_workflows = await get_user_workflows(current_user["id"])
        
        # Get workflows from teams the user is a member of
        from app.db.repositories import WorkflowRepository
        team_workflows = await WorkflowRepository.get_all_by_user_groups(current_user["id"])
        
        # Combine and deduplicate workflows
        all_workflows = own_workflows + team_workflows
        unique_workflows = {}
        
        for workflow in all_workflows:
            workflow_id = workflow["id"]
            if workflow_id not in unique_workflows:
                unique_workflows[workflow_id] = workflow
            else:
                # If workflow appears in both lists, keep the one with more recent updated_at
                existing = unique_workflows[workflow_id]
                if workflow.get("updated_at", "") > existing.get("updated_at", ""):
                    unique_workflows[workflow_id] = workflow
        
        workflows_list = list(unique_workflows.values())
        
        return JSONResponse({
            "success": True,
            "workflows": workflows_list,
            "count": len(workflows_list),
            "own_count": len(own_workflows),
            "team_count": len(team_workflows)
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
    Returns workflows owned by the authenticated user or workflows shared with teams the user is a member of.
    """
    try:
        # First try to get workflow as owner
        workflow = await get_workflow_by_id(workflow_id, current_user["id"])
        
        # If not found as owner, check if accessible through team membership
        if not workflow:
            from app.db.repositories import WorkflowRepository
            team_workflows = await WorkflowRepository.get_all_by_user_groups(current_user["id"])
            workflow = next((w for w in team_workflows if w["id"] == workflow_id), None)
        
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
        # Only owners can delete workflows (not team members)
        workflow = await get_workflow_by_id(workflow_id, current_user["id"])
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found or access denied")
        
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
        # Only owners can update workflows (not team members)
        workflow = await get_workflow_by_id(workflow_id, current_user["id"])
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found or access denied")
        
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
        # Check if user has access to the workflow (owner or team member)
        from app.services.workflow_service import check_workflow_access
        workflow = await check_workflow_access(workflow_id, current_user["id"])
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

@router.post("/{workflow_id}/execute", tags=["Workflow Execution"])
async def execute_workflow_route(
    workflow_id: str,
    execution_type: str = Query("local", pattern="^(local|docker)$"),
    continue_on_failure: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    """
    Execute the entire workflow sequentially.
    - Executes steps in ascending order.
    - Skips steps with is_active = False.
    - Tracks overall status: init, running, completed, failed, partial_failed, completed_with_skips.
    - Persists per-step last execution metadata back into the workflow's steps.
    """
    try:
        started_at = datetime.now()
        overall_status = "init"
        steps_results: List[Dict[str, Any]] = []
        steps_executed = 0
        steps_skipped = 0
        steps_failed = 0

        # Load workflow and authorize
        workflow = await get_workflow_by_id(workflow_id, current_user["id"])
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found or access denied")

        if not workflow.get("is_active", True):
            raise HTTPException(status_code=400, detail="Workflow is not active")

        current_steps: List[Dict[str, Any]] = workflow.get("steps", [])
        # Sort by order (1-based)
        current_steps.sort(key=lambda s: s.get("order") or 0)

        overall_status = "running"

        # Map for updating steps by id later
        step_id_to_index: Dict[str, int] = {s.get("id"): i for i, s in enumerate(current_steps) if s.get("id")}

        for step in current_steps:
            step_id = step.get("id")
            step_name = step.get("name")
            step_order = step.get("order")

            # Skip inactive steps
            if not step.get("is_active", True):
                steps_skipped += 1
                step_result = {
                    "id": step_id,
                    "name": step_name,
                    "order": step_order,
                    "status": "skipped",
                    "reason": "Step is inactive"
                }
                steps_results.append(step_result)

                # Persist minimal metadata
                step["last_status"] = "skipped"
                step["last_run_started_at"] = None
                step["last_run_ended_at"] = None
                step["last_execution_time"] = 0
                step["updated_at"] = datetime.now().isoformat()
                continue

            # Validate prerequisites quickly
            validation = execution_service.validate_execution_prerequisites(workflow, step)
            if not validation["valid"]:
                steps_failed += 1
                step_result = {
                    "id": step_id,
                    "name": step_name,
                    "order": step_order,
                    "status": "failed",
                    "error": validation.get("error")
                }
                steps_results.append(step_result)

                # Persist failure metadata
                now_iso = datetime.now().isoformat()
                step["last_status"] = "failed"
                step["last_run_started_at"] = now_iso
                step["last_run_ended_at"] = now_iso
                step["last_execution_time"] = 0
                step["last_error"] = validation.get("error")
                step["updated_at"] = now_iso

                if not continue_on_failure:
                    overall_status = "failed"
                    break
                else:
                    continue

            # Resolve paths
            step_dir_name = step.get("directory_name")
            if not step_dir_name:
                steps_failed += 1
                err = "Step directory not found"
                step_result = {
                    "id": step_id,
                    "name": step_name,
                    "order": step_order,
                    "status": "failed",
                    "error": err
                }
                steps_results.append(step_result)
                now_iso = datetime.now().isoformat()
                step["last_status"] = "failed"
                step["last_run_started_at"] = now_iso
                step["last_run_ended_at"] = now_iso
                step["last_execution_time"] = 0
                step["last_error"] = err
                step["updated_at"] = now_iso
                if not continue_on_failure:
                    overall_status = "failed"
                    break
                else:
                    continue

            step_dir = file_storage.get_step_directory(workflow_id, step_dir_name)
            if not step_dir:
                steps_failed += 1
                err = "Step directory path not found"
                step_result = {
                    "id": step_id,
                    "name": step_name,
                    "order": step_order,
                    "status": "failed",
                    "error": err
                }
                steps_results.append(step_result)
                now_iso = datetime.now().isoformat()
                step["last_status"] = "failed"
                step["last_run_started_at"] = now_iso
                step["last_run_ended_at"] = now_iso
                step["last_execution_time"] = 0
                step["last_error"] = err
                step["updated_at"] = now_iso
                if not continue_on_failure:
                    overall_status = "failed"
                    break
                else:
                    continue

            script_filename = step.get("script_filename")
            script_path = step_dir / script_filename if script_filename else None
            run_command = step.get("run_command")
            parameters = step.get("parameters", {})
            script_type = str(step.get("script_type", "python"))

            # Execute step
            if execution_type == "docker":
                result = await execution_service.execute_step_in_docker(
                    workflow_id=workflow_id,
                    step_id=step_id,
                    script_path=str(script_path) if script_path else "",
                    run_command=run_command,
                    working_dir=str(step_dir),
                    script_type=script_type,
                    parameters=parameters
                )
            else:
                result = await execution_service.execute_step_locally(
                    workflow_id=workflow_id,
                    step_id=step_id,
                    script_path=str(script_path) if script_path else "",
                    run_command=run_command,
                    working_dir=str(step_dir),
                    parameters=parameters
                )

            steps_executed += 1 if result.get("status") != "skipped" else 0
            if not result.get("success"):
                steps_failed += 1

            # Trim output for storage
            output = result.get("output") or ""
            if isinstance(output, str) and len(output) > 4000:
                output = output[:4000] + "...<truncated>"

            # Persist per-step metadata
            step["last_status"] = result.get("status")
            step["last_return_code"] = result.get("return_code")
            step["last_output"] = output
            step["last_error"] = result.get("error")
            step["last_run_started_at"] = result.get("start_time")
            step["last_run_ended_at"] = result.get("end_time")
            step["last_execution_time"] = result.get("execution_time")
            step["updated_at"] = datetime.now().isoformat()

            steps_results.append({
                "id": step_id,
                "name": step_name,
                "order": step_order,
                "status": result.get("status"),
                "execution_time": result.get("execution_time"),
                "return_code": result.get("return_code"),
                "error": result.get("error"),
                "output": output
            })

            if not result.get("success") and not continue_on_failure:
                overall_status = "failed"
                break

        # Determine overall status if not set to failed already
        ended_at = datetime.now()
        if overall_status != "failed":
            if steps_failed > 0 and continue_on_failure:
                overall_status = "partial_failed"
            elif steps_skipped > 0 and steps_failed == 0:
                overall_status = "completed_with_skips"
            else:
                overall_status = "completed"

        # Persist updated steps back to workflow
        await update_workflow(
            workflow_id=workflow_id,
            user_id=current_user["id"],
            steps=current_steps
        )

        total_time = (ended_at - started_at).total_seconds()
        return JSONResponse({
            "success": overall_status in ("completed", "completed_with_skips"),
            "workflow_id": workflow_id,
            "execution_type": execution_type,
            "status": overall_status,
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
            "total_time": total_time,
            "steps_executed": steps_executed,
            "steps_skipped": steps_skipped,
            "steps_failed": steps_failed,
            "results": steps_results
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 

@router.post("/{workflow_id}/share/groups/{group_id}", tags=["Workflow"])
async def share_workflow_with_group(
    workflow_id: str,
    group_id: str,
    permission: str = Query("read"),
    current_user: dict = Depends(get_current_user)
):
    """
    Share a workflow with a group (owner only). Permissions: read|write|execute (reserved for future use).
    """
    try:
        # Ensure workflow exists and belongs to current user
        workflow = await get_workflow_by_id(workflow_id, current_user["id"])
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found or access denied")
        from app.db.repositories import WorkflowShareRepository
        result = await WorkflowShareRepository.share(workflow_id, group_id, permission)
        if result is None:
            raise HTTPException(status_code=400, detail="Failed to share workflow with group")
        return JSONResponse({
            "success": True,
            "workflow_id": workflow_id,
            "group_id": group_id,
            "permission": permission
        }, status_code=201)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing workflow {workflow_id} with group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{workflow_id}/share/groups/{group_id}", tags=["Workflow"])
async def unshare_workflow_with_group(
    workflow_id: str,
    group_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Remove a workflow's share with a group (owner only).
    """
    try:
        # Ensure workflow exists and belongs to current user
        workflow = await get_workflow_by_id(workflow_id, current_user["id"])
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found or access denied")
        from app.db.repositories import WorkflowShareRepository
        ok = await WorkflowShareRepository.unshare(workflow_id, group_id)
        if not ok:
            raise HTTPException(status_code=400, detail="Failed to unshare workflow with group")
        return JSONResponse({
            "success": True,
            "workflow_id": workflow_id,
            "group_id": group_id
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsharing workflow {workflow_id} from group {group_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 
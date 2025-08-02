from fastapi import APIRouter, Form, Request, Depends, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from app.services.launch_template_service import update_launch_template_from_instance_tag
from app.services.mapping_service import get_all_mappings, create_mapping, update_mapping, delete_mapping
from app.services.workflow_service import create_workflow, get_user_workflows, get_workflow_by_id, delete_workflow, update_workflow, execute_workflow, get_execution_status, get_workflow_executions, get_suggested_dependencies, get_default_run_command, install_dependencies
from app.auth.dependencies import get_current_user
from app.db.models import WorkflowCreate, WorkflowUpdate, ScriptExecutionRequest, DependencyInstallRequest
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflow")

# Existing mapping endpoints
@router.post("/run-json", tags=["Workflow"])
async def run_json(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    server = data.get("server")
    lt = data.get("lt")
    result = update_launch_template_from_instance_tag(server, lt)
    return JSONResponse(result)

@router.get("/get-all-mappings", tags=["Workflow"])
async def api_get_all_mappings(current_user: dict = Depends(get_current_user)):
    mappings = await get_all_mappings()
    return JSONResponse({"mappings": mappings})

@router.post("/create-mapping", tags=["Workflow"])
async def api_create_mapping(request: Request, current_user: dict = Depends(get_current_user)):
    data = await request.json()
    instance = data.get("instance")
    lt_name = data.get("launch_template")
    if not instance or not lt_name:
        return JSONResponse({"error": "Both 'instance' and 'launch_template' are required."}, status_code=400)
    created = await create_mapping(instance, lt_name)
    if not created:
        return JSONResponse({"error": f"Mapping for '{instance}' already exists."}, status_code=409)
    return JSONResponse({"message": f"Created mapping for '{instance}' → '{lt_name}'"})

@router.post("/delete-mapping", response_class=HTMLResponse, tags=["Workflow"])
async def delete_mapping_route(server: str = Form(...), current_user: dict = Depends(get_current_user)):
    success = await delete_mapping(server)
    if success:
        return f"✅ Deleted mapping for <code>{server}</code><br><a href='/settings'>Back</a>"
    else:
        return f"❌ No mapping found for <code>{server}</code><br><a href='/settings'>Back</a>"



# New workflow management endpoints
@router.post("/create", tags=["Workflow"])
async def create_workflow_route(
    workflow_data: WorkflowCreate,
    current_user: dict = Depends(get_current_user)
):


    """
    Create a new workflow for the authenticated user.
    
    Example request body:
    {
        "name": "Deploy to Production",
        "description": "Automated deployment workflow",
        "steps": [
            {"action": "backup", "target": "database"},
            {"action": "deploy", "target": "app"},
            {"action": "health_check", "target": "service"}
        ],
        "script_type": "sh",
        "script_content": "#!/bin/bash\necho 'Hello World'\n",
        "script_filename": "deploy.sh",
        "run_command": "bash deploy.sh",
        "dependencies": ["curl", "jq", "aws-cli"]
    }
    """
    result = await create_workflow(
        user_id=current_user["id"],
        name=workflow_data.name,
        description=workflow_data.description,
        steps=workflow_data.steps,
        script_type=workflow_data.script_type,
        script_content=workflow_data.script_content,
        script_filename=workflow_data.script_filename,
        run_command=workflow_data.run_command,
        dependencies=workflow_data.dependencies,
        is_active=workflow_data.is_active
    )
    

    
    if result["success"]:
        return JSONResponse(result, status_code=201)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@router.post("/upload-script", tags=["Workflow"])
async def upload_script_route(
    name: str = Form(...),
    description: str = Form(""),
    steps: str = Form("[]"),  # JSON string of steps
    script_type: str = Form(...),
    run_command: str = Form(""),
    dependencies: str = Form("[]"),  # JSON string of dependencies
    is_active: bool = Form(True),
    script_file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a workflow by uploading a script file.
    Supports: .sh, .yml, .tf, .py, .js files
    """
    try:
        import json
        
        # Validate script type
        if script_type not in ["sh", "playbook", "terraform", "aws", "python", "node"]:
            raise HTTPException(status_code=400, detail="Invalid script type")
        
        # Read script content
        script_content = await script_file.read()
        script_content = script_content.decode('utf-8')
        
        # Parse steps and dependencies
        try:
            steps_list = json.loads(steps)
        except json.JSONDecodeError:
            steps_list = []
        
        try:
            dependencies_list = json.loads(dependencies)
        except json.JSONDecodeError:
            dependencies_list = []
        
        # Set default run command if not provided
        if not run_command:
            from app.services.dependency_manager import dependency_manager
            run_command = dependency_manager.get_default_run_commands(script_type, script_file.filename)
        
        result = await create_workflow(
            user_id=current_user["id"],
            name=name,
            description=description,
            steps=steps_list,
            script_type=script_type,
            script_content=script_content,
            script_filename=script_file.filename,
            run_command=run_command,
            dependencies=dependencies_list,
            is_active=is_active
        )
        
        if result["success"]:
            return JSONResponse(result, status_code=201)
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error uploading script: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload script")

@router.get("/list", tags=["Workflow"])
async def list_workflows(current_user: dict = Depends(get_current_user)):
    """
    Get all workflows for the authenticated user.
    Returns a list of workflows with their details.
    """
    workflows = await get_user_workflows(current_user["id"])
    return JSONResponse({
        "workflows": workflows,
        "count": len(workflows)
    })

@router.get("/{workflow_id}", tags=["Workflow"])
async def get_workflow_route(
    workflow_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific workflow by ID.
    Only returns workflows owned by the authenticated user.
    """
    workflow = await get_workflow_by_id(workflow_id, current_user["id"])
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found or access denied")
    
    return JSONResponse(workflow)

@router.delete("/{workflow_id}", tags=["Workflow"])
async def delete_workflow_route(
    workflow_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a workflow by ID.
    Only allows deletion of workflows owned by the authenticated user.
    """
    result = await delete_workflow(workflow_id, current_user["id"])
    
    if result["success"]:
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@router.put("/{workflow_id}", tags=["Workflow"])
async def update_workflow_route(
    workflow_id: int,
    workflow_data: WorkflowUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a workflow by ID.
    Only allows updates to workflows owned by the authenticated user.
    
    Example request body (all fields optional):
    {
        "name": "Updated Workflow Name",
        "description": "Updated description",
        "steps": [{"action": "new_step"}],
        "script_type": "sh",
        "script_content": "#!/bin/bash\necho 'Updated script'\n",
        "run_command": "bash updated_script.sh",
        "dependencies": ["curl", "jq"],
        "is_active": false
    }
    """
    result = await update_workflow(
        workflow_id=workflow_id,
        user_id=current_user["id"],
        name=workflow_data.name,
        description=workflow_data.description,
        steps=workflow_data.steps,
        script_type=workflow_data.script_type,
        script_content=workflow_data.script_content,
        script_filename=workflow_data.script_filename,
        run_command=workflow_data.run_command,
        dependencies=workflow_data.dependencies,
        is_active=workflow_data.is_active
    )
    
    if result["success"]:
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

# Script execution endpoints
@router.post("/{workflow_id}/execute", tags=["Workflow"])
async def execute_workflow_route(
    workflow_id: int,
    execution_request: ScriptExecutionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Execute a workflow script.
    
    Example request body:
    {
        "parameters": {"ENV": "production", "VERSION": "1.0.0"},
        "environment": {"AWS_REGION": "us-west-2"},
        "run_command": "bash custom_script.sh"
    }
    """
    result = await execute_workflow(
        workflow_id=workflow_id,
        user_id=current_user["id"],
        parameters=execution_request.parameters,
        environment=execution_request.environment,
        run_command=execution_request.run_command
    )
    
    if result["success"]:
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=400, detail=result["error"])

@router.get("/execution/{execution_id}", tags=["Workflow"])
async def get_execution_status_route(
    execution_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get the status and results of a script execution.
    """
    execution = await get_execution_status(execution_id)
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    # Check if user owns this execution
    if execution["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return JSONResponse(execution)

@router.get("/{workflow_id}/executions", tags=["Workflow"])
async def get_workflow_executions_route(
    workflow_id: int,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """
    Get recent executions for a workflow.
    """
    executions = await get_workflow_executions(workflow_id, current_user["id"], limit)
    return JSONResponse({
        "workflow_id": workflow_id,
        "executions": executions,
        "count": len(executions)
    })

# Dependency management endpoints
@router.get("/suggested-dependencies/{script_type}", tags=["Workflow"])
async def get_suggested_dependencies_route(
    script_type: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get suggested dependencies for a script type.
    """
    dependencies = await get_suggested_dependencies(script_type)
    return JSONResponse({
        "script_type": script_type,
        "suggested_dependencies": dependencies
    })

@router.get("/default-run-command/{script_type}", tags=["Workflow"])
async def get_default_run_command_route(
    script_type: str,
    filename: str = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get default run command for a script type.
    """
    run_command = await get_default_run_command(script_type, filename)
    return JSONResponse({
        "script_type": script_type,
        "filename": filename,
        "default_run_command": run_command
    })

@router.post("/{workflow_id}/install-dependencies", tags=["Workflow"])
async def install_dependencies_route(
    workflow_id: int,
    dependency_request: DependencyInstallRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Install dependencies for a workflow.
    
    Example request body:
    {
        "dependencies": ["curl", "jq", "aws-cli"]
    }
    """
    result = await install_dependencies(
        workflow_id=workflow_id,
        user_id=current_user["id"],
        dependencies=dependency_request.dependencies
    )
    
    if result["success"]:
        return JSONResponse(result)
    else:
        raise HTTPException(status_code=400, detail=result["error"]) 
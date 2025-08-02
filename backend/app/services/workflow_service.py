from app.db.repositories import WorkflowRepository
from app.services.script_executor import script_executor
from app.services.dependency_manager import dependency_manager
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

async def create_workflow(user_id: int, name: str, description: str, steps: list, script_type: str = None, script_content: str = None, script_filename: str = None, run_command: str = None, dependencies: list = None, is_active: bool = True) -> Dict:
    """
    Create a new workflow for a user.
    Returns dict with success status and workflow ID or error message.
    """

    try:
        if not name or not name.strip():
            return {"success": False, "error": "Workflow name is required"}
        
        if not steps or not isinstance(steps, list):
            return {"success": False, "error": "Workflow steps are required and must be a list"}
        
        # Validate script type if provided
        if script_type and script_type not in ["sh", "playbook", "terraform", "aws", "python", "node"]:
            return {"success": False, "error": "Invalid script type. Supported types: sh, playbook, terraform, aws, python, node"}
        
        # Set default run command if not provided
        if script_type and not run_command:
            run_command = dependency_manager.get_default_run_commands(script_type, script_filename)
        
        workflow_id = await WorkflowRepository.create(
            user_id, name.strip(), description, steps, script_type, script_content, script_filename, run_command, dependencies, is_active
        )
        
        if workflow_id:
            return {
                "success": True, 
                "workflow_id": workflow_id,
                "message": f"Workflow '{name}' created successfully"
            }
        else:
            return {"success": False, "error": "Failed to create workflow"}
            
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

async def get_workflow_by_id(workflow_id: int, user_id: int) -> Optional[Dict]:
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

async def delete_workflow(workflow_id: int, user_id: int) -> Dict:
    """
    Delete a workflow by ID for a specific user.
    Returns dict with success status and message.
    """
    try:
        # First check if workflow exists and belongs to user
        workflow = await WorkflowRepository.get_by_id(workflow_id, user_id)
        if not workflow:
            return {"success": False, "error": "Workflow not found or access denied"}
        
        success = await WorkflowRepository.delete(workflow_id, user_id)
        
        if success:
            return {
                "success": True,
                "message": f"Workflow '{workflow['name']}' deleted successfully"
            }
        else:
            return {"success": False, "error": "Failed to delete workflow"}
            
    except Exception as e:
        logger.error(f"Error deleting workflow: {e}")
        return {"success": False, "error": "Internal server error"}

async def update_workflow(workflow_id: int, user_id: int, name: str = None, description: str = None, steps: list = None, script_type: str = None, script_content: str = None, script_filename: str = None, run_command: str = None, dependencies: list = None, is_active: bool = None) -> Dict:
    """
    Update a workflow by ID for a specific user.
    Returns dict with success status and message.
    """
    try:
        # First check if workflow exists and belongs to user
        workflow = await WorkflowRepository.get_by_id(workflow_id, user_id)
        if not workflow:
            return {"success": False, "error": "Workflow not found or access denied"}
        
        # Validate script type if provided
        if script_type and script_type not in ["sh", "playbook", "terraform", "aws", "python", "node"]:
            return {"success": False, "error": "Invalid script type. Supported types: sh, playbook, terraform, aws, python, node"}
        
        # Set default run command if script type changed and no run command provided
        if script_type and not run_command and workflow.get("script_type") != script_type:
            run_command = dependency_manager.get_default_run_commands(script_type, script_filename)
        
        success = await WorkflowRepository.update(
            workflow_id, user_id, name, description, steps, script_type, script_content, script_filename, run_command, dependencies, is_active
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

async def execute_workflow(workflow_id: int, user_id: int, parameters: dict = None, environment: dict = None, run_command: str = None) -> Dict:
    """
    Execute a workflow script.
    Returns dict with execution status and results.
    """
    try:
        # Get workflow details
        workflow = await WorkflowRepository.get_by_id(workflow_id, user_id)
        if not workflow:
            return {"success": False, "error": "Workflow not found or access denied"}
        
        if not workflow.get("script_content"):
            return {"success": False, "error": "Workflow has no script content to execute"}
        
        if not workflow.get("script_type"):
            return {"success": False, "error": "Workflow script type not specified"}
        
        # Use provided run command or workflow's default
        execution_run_command = run_command or workflow.get("run_command")
        
        # Execute the script
        result = await script_executor.execute_script(
            workflow_id=workflow_id,
            user_id=user_id,
            script_type=workflow["script_type"],
            script_content=workflow["script_content"],
            run_command=execution_run_command,
            dependencies=workflow.get("dependencies"),
            parameters=parameters,
            environment=environment
        )
        
        return {
            "success": True,
            "execution_id": result["execution_id"],
            "status": result["status"],
            "output": result.get("output"),
            "error": result.get("error"),
            "exit_code": result.get("exit_code"),
            "execution_time": result.get("execution_time")
        }
        
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        return {"success": False, "error": "Internal server error"}

async def get_execution_status(execution_id: str) -> Optional[Dict]:
    """
    Get the status of a script execution.
    Returns execution details or None if not found.
    """
    try:
        return await script_executor.get_execution_status(execution_id)
    except Exception as e:
        logger.error(f"Error getting execution status: {e}")
        return None

async def get_workflow_executions(workflow_id: int, user_id: int, limit: int = 10) -> List[Dict]:
    """
    Get recent executions for a workflow.
    Returns list of execution records.
    """
    try:
        return await script_executor.get_workflow_executions(workflow_id, user_id, limit)
    except Exception as e:
        logger.error(f"Error getting workflow executions: {e}")
        return []

async def get_suggested_dependencies(script_type: str) -> List[str]:
    """
    Get suggested dependencies for a script type.
    Returns list of suggested dependencies.
    """
    try:
        return dependency_manager.get_suggested_dependencies(script_type)
    except Exception as e:
        logger.error(f"Error getting suggested dependencies: {e}")
        return []

async def get_default_run_command(script_type: str, filename: str = None) -> str:
    """
    Get default run command for a script type.
    Returns default run command string.
    """
    try:
        return dependency_manager.get_default_run_commands(script_type, filename)
    except Exception as e:
        logger.error(f"Error getting default run command: {e}")
        return "bash script.sh"

async def install_dependencies(workflow_id: int, user_id: int, dependencies: list) -> Dict:
    """
    Install dependencies for a workflow.
    Returns installation result.
    """
    try:
        # Get workflow details
        workflow = await WorkflowRepository.get_by_id(workflow_id, user_id)
        if not workflow:
            return {"success": False, "error": "Workflow not found or access denied"}
        
        script_type = workflow.get("script_type", "sh")
        
        # Install dependencies
        if script_type == "python":
            result = await dependency_manager.install_python_dependencies(dependencies)
        elif script_type == "node":
            result = await dependency_manager.install_node_dependencies(dependencies)
        else:
            result = await dependency_manager.install_dependencies(dependencies)
        
        return result
        
    except Exception as e:
        logger.error(f"Error installing dependencies: {e}")
        return {"success": False, "error": "Internal server error"} 
import asyncio
import subprocess
import tempfile
import os
import uuid
import time
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path
import docker
from app.db.repositories import ScriptExecutionRepository

logger = logging.getLogger(__name__)

class ScriptExecutor:
    """Sandboxed script execution service."""
    
    def __init__(self):
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Docker not available: {e}")
    
    async def execute_script(
        self, 
        workflow_id: int, 
        user_id: int, 
        script_type: str, 
        script_content: str, 
        parameters: dict = None, 
        environment: dict = None
    ) -> Dict:
        """
        Execute a script in a sandboxed environment.
        Returns execution result with status, output, and error information.
        """
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Create execution record
            await ScriptExecutionRepository.create_execution(
                execution_id, workflow_id, user_id, parameters, environment
            )
            
            # Execute based on script type
            if script_type == "sh":
                result = await self._execute_shell_script(script_content, parameters, environment)
            elif script_type == "playbook":
                result = await self._execute_ansible_playbook(script_content, parameters, environment)
            elif script_type == "terraform":
                result = await self._execute_terraform(script_content, parameters, environment)
            elif script_type == "aws":
                result = await self._execute_aws_script(script_content, parameters, environment)
            else:
                result = {
                    "status": "failed",
                    "error": f"Unsupported script type: {script_type}",
                    "exit_code": 1
                }
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Update execution record with results
            await ScriptExecutionRepository.update_execution_result(
                execution_id,
                result["status"],
                result.get("output"),
                result.get("error"),
                result.get("exit_code"),
                execution_time
            )
            
            return {
                "execution_id": execution_id,
                "status": result["status"],
                "output": result.get("output"),
                "error": result.get("error"),
                "exit_code": result.get("exit_code"),
                "execution_time": execution_time
            }
            
        except Exception as e:
            logger.error(f"Error executing script: {e}")
            execution_time = time.time() - start_time
            
            # Update execution record with error
            await ScriptExecutionRepository.update_execution_result(
                execution_id,
                "failed",
                None,
                str(e),
                1,
                execution_time
            )
            
            return {
                "execution_id": execution_id,
                "status": "failed",
                "error": str(e),
                "exit_code": 1,
                "execution_time": execution_time
            }
    
    async def _execute_shell_script(self, script_content: str, parameters: dict = None, environment: dict = None) -> Dict:
        """Execute a shell script in a sandboxed environment."""
        if self.docker_client:
            return await self._execute_in_docker("alpine:latest", script_content, parameters, environment)
        else:
            return await self._execute_locally(script_content, parameters, environment)
    
    async def _execute_ansible_playbook(self, playbook_content: str, parameters: dict = None, environment: dict = None) -> Dict:
        """Execute an Ansible playbook in a sandboxed environment."""
        if self.docker_client:
            return await self._execute_in_docker("ansible/ansible-runner:latest", playbook_content, parameters, environment, "ansible-playbook")
        else:
            return await self._execute_locally(playbook_content, parameters, environment, "ansible-playbook")
    
    async def _execute_terraform(self, terraform_content: str, parameters: dict = None, environment: dict = None) -> Dict:
        """Execute Terraform code in a sandboxed environment."""
        if self.docker_client:
            return await self._execute_in_docker("hashicorp/terraform:latest", terraform_content, parameters, environment, "terraform")
        else:
            return await self._execute_locally(terraform_content, parameters, environment, "terraform")
    
    async def _execute_aws_script(self, aws_content: str, parameters: dict = None, environment: dict = None) -> Dict:
        """Execute AWS CLI commands in a sandboxed environment."""
        if self.docker_client:
            return await self._execute_in_docker("amazon/aws-cli:latest", aws_content, parameters, environment)
        else:
            return await self._execute_locally(aws_content, parameters, environment)
    
    async def _execute_in_docker(self, image: str, script_content: str, parameters: dict = None, environment: dict = None, command: str = None) -> Dict:
        """Execute script in Docker container."""
        try:
            # Create temporary directory for script
            with tempfile.TemporaryDirectory() as temp_dir:
                script_path = Path(temp_dir) / "script"
                
                # Write script content to file
                with open(script_path, 'w') as f:
                    f.write(script_content)
                os.chmod(script_path, 0o755)
                
                # Prepare environment variables
                env_vars = environment or {}
                if parameters:
                    env_vars.update(parameters)
                
                # Execute in Docker container
                container = self.docker_client.containers.run(
                    image,
                    command=f"{command} {script_path}" if command else f"/bin/sh {script_path}",
                    environment=env_vars,
                    volumes={temp_dir: {'bind': '/workspace', 'mode': 'ro'}},
                    working_dir='/workspace',
                    detach=True,
                    remove=True,
                    network_mode='none',  # Isolated network
                    mem_limit='512m',      # Memory limit
                    cpu_period=100000,     # CPU limit
                    cpu_quota=50000,       # 50% CPU
                    security_opt=['no-new-privileges'],  # Security option
                    read_only=True         # Read-only filesystem
                )
                
                # Wait for completion with timeout
                try:
                    result = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, container.wait),
                        timeout=300  # 5 minutes timeout
                    )
                    
                    logs = container.logs().decode('utf-8')
                    
                    return {
                        "status": "completed" if result['StatusCode'] == 0 else "failed",
                        "output": logs,
                        "error": None if result['StatusCode'] == 0 else logs,
                        "exit_code": result['StatusCode']
                    }
                    
                except asyncio.TimeoutError:
                    container.kill()
                    return {
                        "status": "failed",
                        "error": "Execution timeout (5 minutes)",
                        "exit_code": 124
                    }
                    
        except Exception as e:
            logger.error(f"Error executing in Docker: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "exit_code": 1
            }
    
    async def _execute_locally(self, script_content: str, parameters: dict = None, environment: dict = None, command: str = None) -> Dict:
        """Execute script locally (fallback when Docker is not available)."""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as temp_file:
                temp_file.write(script_content)
                temp_file_path = temp_file.name
            
            try:
                # Prepare environment
                env = os.environ.copy()
                if environment:
                    env.update(environment)
                if parameters:
                    env.update(parameters)
                
                # Execute script
                if command:
                    cmd = [command, temp_file_path]
                else:
                    cmd = ['/bin/bash', temp_file_path]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env
                )
                
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
                
                output = stdout.decode('utf-8')
                error = stderr.decode('utf-8')
                
                return {
                    "status": "completed" if process.returncode == 0 else "failed",
                    "output": output,
                    "error": error if process.returncode != 0 else None,
                    "exit_code": process.returncode
                }
                
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except asyncio.TimeoutError:
            return {
                "status": "failed",
                "error": "Execution timeout (5 minutes)",
                "exit_code": 124
            }
        except Exception as e:
            logger.error(f"Error executing locally: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "exit_code": 1
            }
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict]:
        """Get the status of a script execution."""
        return await ScriptExecutionRepository.get_execution(execution_id)
    
    async def get_workflow_executions(self, workflow_id: int, user_id: int, limit: int = 10) -> list:
        """Get recent executions for a workflow."""
        return await ScriptExecutionRepository.get_executions_by_workflow(workflow_id, user_id, limit)

# Global script executor instance
script_executor = ScriptExecutor() 
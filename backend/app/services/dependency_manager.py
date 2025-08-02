import asyncio
import logging
from typing import Dict, List, Optional
import docker
from app.db.repositories import ScriptExecutionRepository

logger = logging.getLogger(__name__)

class DependencyManager:
    """Manages dependency installation in sandboxed environments."""
    
    def __init__(self):
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Docker not available: {e}")
    
    async def install_dependencies(self, dependencies: List[str], base_image: str = "alpine:latest") -> Dict:
        """
        Install dependencies in a sandboxed environment.
        Returns installation result with success status and details.
        """
        if not self.docker_client:
            return {
                "success": False,
                "error": "Docker not available for dependency installation",
                "installed": [],
                "failed": dependencies
            }
        
        try:
            # Create a temporary container to install dependencies
            container = self.docker_client.containers.run(
                base_image,
                command="sh -c 'apk update && apk add --no-cache " + " ".join(dependencies) + "'",
                detach=True,
                remove=True,
                network_mode='none',
                mem_limit='256m',
                cpu_period=100000,
                cpu_quota=25000,  # 25% CPU
                security_opt=['no-new-privileges'],
                read_only=False  # Need write access for installation
            )
            
            # Wait for installation with timeout
            try:
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, container.wait),
                    timeout=300  # 5 minutes timeout
                )
                
                logs = container.logs().decode('utf-8')
                
                if result['StatusCode'] == 0:
                    return {
                        "success": True,
                        "message": "Dependencies installed successfully",
                        "installed": dependencies,
                        "failed": [],
                        "logs": logs
                    }
                else:
                    return {
                        "success": False,
                        "error": "Dependency installation failed",
                        "installed": [],
                        "failed": dependencies,
                        "logs": logs
                    }
                    
            except asyncio.TimeoutError:
                container.kill()
                return {
                    "success": False,
                    "error": "Dependency installation timeout",
                    "installed": [],
                    "failed": dependencies
                }
                
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return {
                "success": False,
                "error": str(e),
                "installed": [],
                "failed": dependencies
            }
    
    async def install_python_dependencies(self, requirements: List[str]) -> Dict:
        """Install Python dependencies using pip."""
        if not self.docker_client:
            return {
                "success": False,
                "error": "Docker not available for dependency installation",
                "installed": [],
                "failed": requirements
            }
        
        try:
            # Create requirements.txt content
            requirements_content = "\n".join(requirements)
            
            # Create a temporary container to install Python dependencies
            container = self.docker_client.containers.run(
                "python:3.11-slim",
                command=f"sh -c 'echo \"{requirements_content}\" > requirements.txt && pip install -r requirements.txt'",
                detach=True,
                remove=True,
                network_mode='none',
                mem_limit='512m',
                cpu_period=100000,
                cpu_quota=25000,
                security_opt=['no-new-privileges'],
                read_only=False
            )
            
            # Wait for installation with timeout
            try:
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, container.wait),
                    timeout=600  # 10 minutes timeout for Python packages
                )
                
                logs = container.logs().decode('utf-8')
                
                if result['StatusCode'] == 0:
                    return {
                        "success": True,
                        "message": "Python dependencies installed successfully",
                        "installed": requirements,
                        "failed": [],
                        "logs": logs
                    }
                else:
                    return {
                        "success": False,
                        "error": "Python dependency installation failed",
                        "installed": [],
                        "failed": requirements,
                        "logs": logs
                    }
                    
            except asyncio.TimeoutError:
                container.kill()
                return {
                    "success": False,
                    "error": "Python dependency installation timeout",
                    "installed": [],
                    "failed": requirements
                }
                
        except Exception as e:
            logger.error(f"Error installing Python dependencies: {e}")
            return {
                "success": False,
                "error": str(e),
                "installed": [],
                "failed": requirements
            }
    
    async def install_node_dependencies(self, packages: List[str]) -> Dict:
        """Install Node.js dependencies using npm."""
        if not self.docker_client:
            return {
                "success": False,
                "error": "Docker not available for dependency installation",
                "installed": [],
                "failed": packages
            }
        
        try:
            # Create package.json content
            package_json = {
                "name": "workflow-dependencies",
                "version": "1.0.0",
                "dependencies": {pkg: "*" for pkg in packages}
            }
            
            import json
            package_json_content = json.dumps(package_json)
            
            # Create a temporary container to install Node.js dependencies
            container = self.docker_client.containers.run(
                "node:18-alpine",
                command=f"sh -c 'echo \"{package_json_content}\" > package.json && npm install'",
                detach=True,
                remove=True,
                network_mode='none',
                mem_limit='512m',
                cpu_period=100000,
                cpu_quota=25000,
                security_opt=['no-new-privileges'],
                read_only=False
            )
            
            # Wait for installation with timeout
            try:
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(None, container.wait),
                    timeout=600  # 10 minutes timeout for Node.js packages
                )
                
                logs = container.logs().decode('utf-8')
                
                if result['StatusCode'] == 0:
                    return {
                        "success": True,
                        "message": "Node.js dependencies installed successfully",
                        "installed": packages,
                        "failed": [],
                        "logs": logs
                    }
                else:
                    return {
                        "success": False,
                        "error": "Node.js dependency installation failed",
                        "installed": [],
                        "failed": packages,
                        "logs": logs
                    }
                    
            except asyncio.TimeoutError:
                container.kill()
                return {
                    "success": False,
                    "error": "Node.js dependency installation timeout",
                    "installed": [],
                    "failed": packages
                }
                
        except Exception as e:
            logger.error(f"Error installing Node.js dependencies: {e}")
            return {
                "success": False,
                "error": str(e),
                "installed": [],
                "failed": packages
            }
    
    def get_suggested_dependencies(self, script_type: str) -> List[str]:
        """Get suggested dependencies based on script type."""
        suggestions = {
            "sh": [
                "curl", "wget", "jq", "git", "docker", "kubectl",
                "aws-cli", "gcloud", "az", "terraform"
            ],
            "playbook": [
                "ansible", "ansible-core", "ansible-runner"
            ],
            "terraform": [
                "terraform", "terraform-docs", "tflint"
            ],
            "aws": [
                "aws-cli", "aws-vault", "aws-iam-authenticator"
            ],
            "python": [
                "requests", "boto3", "kubernetes", "docker",
                "fastapi", "pandas", "numpy"
            ],
            "node": [
                "axios", "aws-sdk", "kubernetes-client",
                "express", "jest", "typescript"
            ]
        }
        
        return suggestions.get(script_type, [])
    
    def get_default_run_commands(self, script_type: str, filename: str = None) -> str:
        """Get default run commands based on script type."""
        commands = {
            "sh": "bash script.sh",
            "playbook": "ansible-playbook playbook.yml",
            "terraform": "terraform apply",
            "aws": "bash script.sh",
            "python": "python script.py",
            "node": "node script.js"
        }
        
        if filename:
            # Replace generic names with actual filename
            if script_type == "sh":
                return f"bash {filename}"
            elif script_type == "playbook":
                return f"ansible-playbook {filename}"
            elif script_type == "terraform":
                return f"terraform apply {filename}"
            elif script_type == "python":
                return f"python {filename}"
            elif script_type == "node":
                return f"node {filename}"
        
        return commands.get(script_type, "bash script.sh")

# Global dependency manager instance
dependency_manager = DependencyManager() 
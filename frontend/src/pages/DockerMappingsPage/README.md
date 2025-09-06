# Docker Mappings Page

A dedicated page for managing Docker execution mappings for different script types.

## Features

- **Create Docker Mappings**: Add new Docker mappings with script type, image, tag, description, environment variables, volumes, and ports
- **List Docker Mappings**: View all Docker mappings in a clean, organized table
- **Edit Docker Mappings**: Modify existing Docker mappings
- **Delete Docker Mappings**: Remove Docker mappings with confirmation
- **View Details**: Detailed view of each Docker mapping with all configuration options
- **Status Management**: Enable/disable Docker mappings

## API Endpoints Used

- `POST /config/docker-mappings` - Create Docker mapping
- `GET /config/docker-mappings` - List all Docker mappings
- `GET /config/docker-mappings/{mapping_id}` - Get specific Docker mapping
- `PUT /config/docker-mappings/{mapping_id}` - Update Docker mapping
- `DELETE /config/docker-mappings/{mapping_id}` - Delete Docker mapping

## Request Body Example

```json
{
  "script_type": "python",
  "docker_image": "custom-python:3.9",
  "docker_tag": "latest",
  "description": "Custom Python 3.9 environment",
  "environment_variables": {
    "PYTHONPATH": "/app"
  },
  "volumes": ["/host/data:/container/data"],
  "ports": ["8080:8080"],
  "is_active": true
}
```

## Supported Script Types

- Python
- Node.js
- Ansible
- Terraform
- Shell (sh, bash, zsh)
- PowerShell
- Go
- Rust
- Java
- C#

## Navigation

Access the Docker Mappings page via:
- Sidebar: Configurations → Docker Mappings (Dedicated)
- Direct URL: `/docker-mappings`

## Components

- `DockerMappingsPage.tsx` - Main page component
- `DockerMappingsPage.css` - Styling
- `index.tsx` - Export file

## Features

- **Responsive Design**: Works on desktop and mobile devices
- **Modern UI**: Clean, intuitive interface with proper styling
- **Error Handling**: Comprehensive error handling with user-friendly messages
- **Loading States**: Loading indicators for better UX
- **Confirmation Dialogs**: Safe deletion with confirmation
- **Form Validation**: Proper validation for required fields
- **Real-time Updates**: Automatic refresh after operations 
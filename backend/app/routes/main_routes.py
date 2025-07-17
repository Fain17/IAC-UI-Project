from fastapi import APIRouter, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from app.services.launch_template_service import update_launch_template_from_instance_tag
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "iac-ui-agent"}
    )


@router.get("/", response_class=HTMLResponse)
async def form(current_user: dict = Depends(get_current_user)):
    """Main form page for creating AMI and updating launch template."""
    return f"""
        <h2>Welcome, {current_user['username']}!</h2>
        <form action="/run" method="post">
            EC2 Name Tag: <input type="text" name="server"><br>
            Launch Template Name: <input type="text" name="lt"><br>
            <input type="submit" value="Create AMI & Update LT">
        </form>
        <p><a href="/auth/logout">Logout</a></p>
    """


@router.post("/run", response_class=HTMLResponse)
async def run(server: str = Form(...), lt: str = Form(...), current_user: dict = Depends(get_current_user)):
    """Handle form submission for AMI creation and launch template update."""
    result = update_launch_template_from_instance_tag(server, lt)
    
    if result["success"]:
        return f"""
        ✅ Success!<br>
        AMI ID: <code>{result['ami_id']}</code><br>
        LT ID: <code>{result['launch_template_id']}</code><br>
        New Version: <code>{result['new_version']}</code><br>
        <a href='/'>Back</a>
        """
    else:
        return f"❌ Error: {result['error']}<br><a href='/'>Back</a>" 
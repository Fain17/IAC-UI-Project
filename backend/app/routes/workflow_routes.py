from fastapi import APIRouter, Form, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from app.services.launch_template_service import update_launch_template_from_instance_tag
from app.services.mapping_service import get_all_mappings, create_mapping, update_mapping, delete_mapping
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/workflow")

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
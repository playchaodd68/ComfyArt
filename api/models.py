import os

import folder_paths
from aiohttp import web

from ._common import error, json_body, routes
from .model_registry import catalog, resolve_graph


def model_paths() -> dict[str, str]:
    paths: dict[str, str] = {}
    for folder, (_, extensions) in folder_paths.folder_names_and_paths.items():
        if folder_paths.supported_pt_extensions.isdisjoint(extensions):
            continue
        names = folder_paths.get_filename_list(folder)
        root = {n for n in names if os.path.basename(n) == n}
        for name in names:
            base = os.path.basename(name.replace("\\", "/"))
            if base != name and base not in root:
                paths.setdefault(base, name)
    return paths


@routes.get("/comfyart/model-paths")
async def get_model_paths(request: web.Request) -> web.Response:
    return web.json_response(model_paths())


@routes.get("/comfyart/model-catalog")
async def get_model_catalog(_request: web.Request) -> web.Response:
    return web.json_response(catalog())


@routes.post("/comfyart/resolve-workflow")
async def resolve_workflow(request: web.Request) -> web.Response:
    body = await json_body(request)
    graph = body.get("graph")
    if not isinstance(graph, dict) or not graph or len(graph) > 1000:
        return error("graph must contain between 1 and 1000 nodes", 400)
    try:
        graph, bindings, missing = resolve_graph(graph)
    except ValueError as exc:
        return error(str(exc), 400)
    if missing:
        return web.json_response({"error": "; ".join(missing), "missing": missing}, status=400)
    return web.json_response({"graph": graph, "bindings": bindings})

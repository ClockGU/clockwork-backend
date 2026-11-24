import warnings
from fastapi.routing import APIRoute

from api.security import get_current_student, get_current_supervisor, get_current_clerk, get_current_clerk_or_student

PERMISSION_FUNCS = {
    "CLERK": get_current_clerk,
    "STUDENT": get_current_student,
    "SUPERVISOR": get_current_supervisor,
    "STUDENT_OR_CLERK": get_current_clerk_or_student,
}
IGNORE_ROUTES = {
    "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc", "/admin","/ws/{client_id}",
    # BudgetPosition endpoints do not have assigned permission guards since they do not log in
    "/approver/petitions/{petition_id}/{signature}/{budget_position_id}"
}
EXPECTED_PERMISSIONS = {
    # StudentDocument endpoints
    "/documents": {"GET": "STUDENT"},
    "/documents/{document_id}": {"PATCH": "STUDENT"},
    "/documents/{document_id}/{document_type}": {"GET": "STUDENT_OR_CLERK"},
    "/clerk/petitions/{petition_id}/documents": {"GET": "CLERK"},
    # Employee endpoints
    "/employees/me": {"GET": "STUDENT"},
    "/employees/{username}": {"GET": "CLERK"},
    "/employees/{employee_id}": {"PATCH": "STUDENT"},
    # Petition endpoints
    "/clerk/petitions/{petition_id}": {"DELETE": "CLERK", "PATCH": "CLERK"},
    "/clerk/petitions/{petition_id}/request-revision": {"PATCH": "CLERK"},
    "/clerk/petitions/{petition_id}/student-data-pdf": {"GET": "CLERK"},
    "/students/petitions": {"GET": "STUDENT"},
    "/students/petitions/{petition_id}/student-action": {"PATCH": "STUDENT"},
    "/students/petitions/{petition_id}/request-revision": {"PATCH": "STUDENT"},
    "/supervisor/petitions": {"POST": "SUPERVISOR","GET": "SUPERVISOR"},
    "/supervisor/petitions/{petition_id}": {"GET": "SUPERVISOR","PATCH": "SUPERVISOR","DELETE": "SUPERVISOR"},
    # PrevEmployments
    "/prev_employments": {"POST": "STUDENT","GET": "STUDENT_OR_CLERK"},
    "/prev_employments/{prev_employment_id}/proof": {"GET": "STUDENT"},
    "/prev_employments/{prev_employment_id}": {"DELETE":"STUDENT","PATCH": "STUDENT"},
    "/clerk/prev_employments/petition/{petition_id}": {"GET": "CLERK"},
    "/clerk/prev_employments/{prev_employment_id}/download": {"GET": "CLERK"},

}

def test_route_permission_test():
    from api.main import app

    for route in app.routes:
        if route.path in IGNORE_ROUTES:
            continue
        if not isinstance(route, APIRoute):
            warnings.warn(f"A non-APIRoute with path {route.path} not present in IGNORE_ROUTES was encountered and skipped.",UserWarning, stacklevel=2)
            continue
        expected_methods = EXPECTED_PERMISSIONS.get(route.path)
        if not expected_methods:
            raise Exception(f"The route with path {route.path} and method {route.methods} has "
                            "neither defined expected permissions nor is it specified as an IGNORE_ROUTE.")
        route_method = list(route.methods)[0]
        method_permission = expected_methods.get(route_method)
        if not method_permission:
            raise Exception(
                f"The route with path {route.path} does not specify expected permissions for the implemented method {route_method}."
            )

        permission_check_fn = PERMISSION_FUNCS.get(method_permission)
        if not any([dep.call == permission_check_fn for dep in route.dependant.dependencies]):
            raise Exception(f"The route with path {route.path} and method {route.methods} is not guarded "
                            f"by a role check for role {method_permission} with function {permission_check_fn.__name__}")

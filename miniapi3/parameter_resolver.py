import inspect
import json

from .request import Request
from .validation import ValidationError


class ParameterResolver:
    @staticmethod
    async def resolve_params(handler, request: Request, debug: bool = False):
        sig = inspect.signature(handler)
        params = {}

        try:
            if debug:
                print(f"Handler parameters: {sig.parameters}")
                print(f"Request body: {await request.text()}")
                print(f"Query params: {request.query_params}")

            for name, param in sig.parameters.items():
                annotation = param.annotation

                if debug:
                    print(f"Processing parameter {name} with annotation {annotation}")

                # Handle path parameters
                if name in request.path_params:
                    value = request.path_params[name]
                    if annotation != inspect.Parameter.empty:
                        try:
                            value = annotation(value)
                        except ValueError as e:
                            raise ValidationError(f"Invalid type for parameter {name}: {str(e)}")
                    params[name] = value
                    continue

                # Handle query parameters
                if name in request.query_params:
                    value = request.query_params[name][0]  # Get first value
                    if annotation != inspect.Parameter.empty:
                        try:
                            value = annotation(value)
                        except ValueError as e:
                            raise ValidationError(f"Invalid type for parameter {name}: {str(e)}")
                    params[name] = value
                    continue

                # Handle request object injection
                if annotation == Request:
                    params[name] = request
                    continue

                # Handle Pydantic models
                if hasattr(annotation, "model_validate"):
                    try:
                        if not hasattr(request, "_cached_json"):
                            request._cached_json = await request.json()
                        data = request._cached_json
                        params[name] = annotation.model_validate(data)
                        continue
                    except json.JSONDecodeError:
                        raise ValidationError("Invalid JSON data")
                    except Exception as e:
                        raise ValidationError(f"Validation error for {name}: {str(e)}")

                # If parameter is required but not found, raise an error
                if param.default == inspect.Parameter.empty:
                    raise ValidationError(f"Missing required parameter: {name}")

            if debug:
                print(f"Final resolved params: {params}")

            return params
        except Exception as e:
            if debug:
                print(f"Error in _resolve_params: {str(e)}")
            raise

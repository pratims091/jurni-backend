
import os
import sys
from firebase_functions import https_fn, options
from firebase_admin import initialize_app

os.environ.setdefault("GOOGLE_CLOUD_DISABLE_GRPC", "true")

if '.' not in sys.path:
    sys.path.insert(0, '.')
if os.path.dirname(__file__) not in sys.path:
    sys.path.insert(0, os.path.dirname(__file__))

try:
    initialize_app()
except ValueError:
    pass

from app.main import app


@https_fn.on_request(
    cors=options.CorsOptions(
        cors_origins=["*"],
        cors_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ),
    memory=512,
    timeout_sec=300
)
def jurni_api(req: https_fn.Request) -> https_fn.Response:
    import asyncio
    import json
    from typing import Dict, Any
    
    def firebase_to_asgi_event(request):
        """Convert Firebase Functions request to AWS Lambda-like event format"""
        headers = dict(request.headers)
        
        body = ""
        if request.data:
            body = request.data.decode('utf-8') if isinstance(request.data, bytes) else str(request.data)
        elif hasattr(request, 'get_data'):
            body_bytes = request.get_data()
            body = body_bytes.decode('utf-8') if body_bytes else ""
        
        path = request.path.rstrip('/') if request.path != '/' else '/'
            
        return {
            "version": "2.0",
            "routeKey": f"{request.method} {path}",
            "rawPath": path,
            "rawQueryString": request.query_string.decode('utf-8') if request.query_string else "",
            "headers": headers,
            "queryStringParameters": dict(request.args) if request.args else None,
            "body": body,
            "isBase64Encoded": False,
            "requestContext": {
                "accountId": "123456789012",
                "apiId": "firebase-functions",
                "domainName": request.host,
                "domainPrefix": "api",
                "http": {
                    "method": request.method,
                    "path": path,
                    "protocol": "HTTP/1.1",
                    "sourceIp": request.remote_addr or "127.0.0.1",
                    "userAgent": headers.get('user-agent', '')
                },
                "requestId": "firebase-functions-request",
                "routeKey": f"{request.method} {path}",
                "stage": "$default",
                "time": "01/Jan/2024:00:00:00 +0000",
                "timeEpoch": 1704067200000
            },
            "httpMethod": request.method,
            "path": path,
            "resource": "/{proxy+}",
            "pathParameters": None,
            "stageVariables": None
        }
    
    def asgi_to_firebase_response(response):
        from flask import Response
        
        status_code = response.get("statusCode", 200)
        headers = response.get("headers", {})
        body = response.get("body", "")
        
        return Response(
            body,
            status=status_code,
            headers=headers
        )
    
    try:
        from mangum import Mangum
        
        handler = Mangum(
            app,
            lifespan="off",
            api_gateway_base_path=None,
            text_mime_types=[
                "application/json",
                "application/javascript",
                "application/xml",
                "application/vnd.api+json",
            ]
        )
        
        event = firebase_to_asgi_event(req)
        context = {"aws_request_id": "firebase-functions"}
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        try:
            response = handler(event, context)
        finally:
            if loop.is_running() is False:
                loop.close()
                asyncio.set_event_loop(None)
        
        return asgi_to_firebase_response(response)
        
    except Exception as e:
        from flask import jsonify
        import traceback
        
        print(f"Error in jurni_api: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

from coraza import Coraza
from coraza.http import CorazaHttp
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import os

class WAFMiddleware:
    def __init__(self):
        self.waf = Coraza()
        self.waf_http = CorazaHttp(self.waf)
        self.rule_dir = "waf/rules"
        self.load_rules()
    
    def load_rules(self):
        if os.path.exists(self.rule_dir):
            for rule_file in os.listdir(self.rule_dir):
                if rule_file.endswith(".conf"):
                    with open(os.path.join(self.rule_dir, rule_file), "r") as f:
                        self.waf.load_rules(f.read())
    
    async def process(self, request: Request, call_next):
        try:
            # Process request through WAF
            tx = self.waf_http.new_transaction(request)
            
            # Check if blocked
            if tx.interrupted:
                return JSONResponse(
                    status_code=403,
                    content={"error": "Request blocked by WAF", "rule_id": tx.rule_id}
                )
            
            # Continue to app
            response = await call_next(request)
            
            # Process response through WAF
            tx.process_response(response)
            
            if tx.interrupted:
                return JSONResponse(
                    status_code=403,
                    content={"error": "Response blocked by WAF"}
                )
            
            return response
            
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"WAF error: {str(e)}"}
            )

waf_middleware = WAFMiddleware()

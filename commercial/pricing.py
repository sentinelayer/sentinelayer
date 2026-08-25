#!/usr/bin/env python3
"""
SentinelLayer Pricing Calculator
"""

import json
from typing import Dict, Any

class PricingCalculator:
    def __init__(self):
        self.tiers = {
            "startup": {
                "name": "Startup",
                "price": 299,
                "requests": 100000,
                "features": ["WAF", "Rate Limiting", "Basic Analytics"]
            },
            "business": {
                "name": "Business",
                "price": 999,
                "requests": 500000,
                "features": ["WAF", "Rate Limiting", "Analytics", "Behavior Engine"]
            },
            "enterprise": {
                "name": "Enterprise",
                "price": 4999,
                "requests": 5000000,
                "features": ["All Features", "Dedicated Support", "SLA"]
            }
        }
    
    def calculate(self, requests_per_month: int, features: list) -> Dict[str, Any]:
        """Calculate pricing based on usage"""
        
        result = {
            "tier": None,
            "price": 0,
            "features": [],
            "custom": False
        }
        
        # Find appropriate tier
        for tier_name, tier in self.tiers.items():
            if requests_per_month <= tier["requests"]:
                result["tier"] = tier_name
                result["price"] = tier["price"]
                result["features"] = tier["features"]
                result["custom"] = False
                return result
        
        # Custom pricing for high volume
        extra_requests = requests_per_month - self.tiers["enterprise"]["requests"]
        extra_cost = (extra_requests / 1000000) * 99  # $99 per million extra
        
        result["tier"] = "enterprise"
        result["price"] = self.tiers["enterprise"]["price"] + extra_cost
        result["features"] = self.tiers["enterprise"]["features"]
        result["custom"] = True
        
        return result
    
    def get_yearly_price(self, monthly_price: float) -> float:
        """Calculate yearly price (2 months free)"""
        return monthly_price * 10  # 12 months - 2 free
    
    def generate_quote(self, company_name: str, requests_per_month: int, features: list) -> str:
        """Generate a pricing quote"""
        
        pricing = self.calculate(requests_per_month, features)
        
        quote = f"""
==========================================================================
SENTINELLAYER - PRICING QUOTE
==========================================================================

Company: {company_name}
Monthly Requests: {requests_per_month:,}
Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}

---
Tier: {pricing['tier'].upper()}
Monthly Price: ${pricing['price']:,.2f}/month
Yearly Price: ${self.get_yearly_price(pricing['price']):,.2f}/year
---

Included Features:
{chr(10).join('  ✅ ' + f for f in pricing['features'])}

{'✅ Custom pricing applied for volume discount' if pricing['custom'] else ''}

Terms:
- Billing: Monthly or Annual
- Payment: Credit Card or Invoice
- Support: Email + Chat (Business hours)
- SLA: 99.9% uptime
- No long-term contract required

Contact: sales@sentinelayer.com
==========================================================================
"""
        return quote

if __name__ == "__main__":
    calc = PricingCalculator()
    
    # Example quotes
    print(calc.generate_quote("Acme Corp", 100000, []))
    print(calc.generate_quote("TechCo Inc", 500000, []))
    print(calc.generate_quote("Enterprise Inc", 10000000, []))

"""
Test suite for ranking engine
Run with: pytest test_ranking.py -v
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from ranking_engine import RankingEngine

# Test client for API
client = TestClient(app)

# Test engine directly
engine = RankingEngine()

class TestRankingEngine:
    """Test the core ranking logic"""
    
    def test_exact_match_scores_high(self):
        """Exact product matches should score > 0.7"""
        products = [
            {"name": "Corn on the Cob", "brand": "Fresh"},
            {"name": "Pogo Corn Dogs", "brand": "Pogo"}
        ]
        
        scores = engine.score_products("corn", products)
        
        # Find corn on the cob score
        corn_cob = next(s for s in scores if "Corn on the Cob" in s["product_name"])
        assert corn_cob["relevance"] > 0.7, "Exact match should score high"
    
    def test_irrelevant_products_score_low(self):
        """Obviously wrong products should score < 0.3"""
        products = [
            {"name": "Pogo Corn Dogs", "brand": "Pogo"},
            {"name": "Corn Chips", "brand": "Tostitos"}
        ]
        
        scores = engine.score_products("corn on the cob", products)
        
        for score in scores:
            assert score["relevance"] < 0.3, f"{score['product_name']} should score low"
    
    def test_bulk_items_deprioritized(self):
        """Bulk items should score lower unless bulk is requested"""
        products = [
            {"name": "Eggs Large Dozen", "brand": "Burnbrae"},
            {"name": "Eggs Case of 24 Dozen", "brand": "Burnbrae"}
        ]
        
        scores = engine.score_products("eggs", products)
        
        single = next(s for s in scores if "Case" not in s["product_name"])
        bulk = next(s for s in scores if "Case" in s["product_name"])
        
        assert single["relevance"] > bulk["relevance"], "Single items should rank higher than bulk"
    
    def test_category_understanding(self):
        """Should understand product categories"""
        products = [
            {"name": "2% Milk", "brand": "Neilson"},
            {"name": "Almond Milk", "brand": "Silk"},
            {"name": "Milk Chocolate Bar", "brand": "Cadbury"}
        ]
        
        scores = engine.score_products("milk", products)
        
        # Real milk should score highest
        dairy_milk = next(s for s in scores if "2% Milk" in s["product_name"])
        chocolate = next(s for s in scores if "Chocolate" in s["product_name"])
        
        assert dairy_milk["relevance"] > chocolate["relevance"], "Dairy milk should outrank chocolate"

class TestAPI:
    """Test the API endpoints"""
    
    def test_health_check(self):
        """Health endpoint should return 200"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_ranking_endpoint(self):
        """Ranking endpoint should return scores"""
        request_data = {
            "search_term": "apples",
            "products": [
                {"name": "Gala Apples", "brand": "Fresh", "price": 4.99},
                {"name": "Apple Juice", "brand": "Tropicana", "price": 3.99},
                {"name": "Apple Pie", "brand": "Store Made", "price": 8.99}
            ]
        }
        
        response = client.post("/rank", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "scores" in data
        assert "metadata" in data
        assert len(data["scores"]) == 3
    
    def test_confidence_levels(self):
        """Should return appropriate confidence levels"""
        request_data = {
            "search_term": "very specific purple dragon fruit",
            "products": [
                {"name": "Bananas", "brand": "Dole"},
                {"name": "Dragon Fruit", "brand": "Fresh"}
            ]
        }
        
        response = client.post("/rank", json=request_data)
        data = response.json()
        
        # At least one should have low confidence for weird search
        confidences = [s["confidence"] for s in data["scores"]]
        assert "low" in confidences or "medium" in confidences

class TestEdgeCases:
    """Test edge cases and tricky scenarios"""
    
    def test_common_problematic_searches(self):
        """Test searches that often return wrong results"""
        test_cases = [
            {
                "search": "corn",
                "right": "Sweet Corn on the Cob",
                "wrong": "Pogo Corn Dogs"
            },
            {
                "search": "cream",
                "right": "Heavy Cream 35%",
                "wrong": "Ice Cream"
            },
            {
                "search": "butter",
                "right": "Salted Butter",
                "wrong": "Peanut Butter"
            }
        ]
        
        for test in test_cases:
            products = [
                {"name": test["right"], "brand": "Generic"},
                {"name": test["wrong"], "brand": "Generic"}
            ]
            
            scores = engine.score_products(test["search"], products)
            
            right_score = next(s for s in scores if test["right"] in s["product_name"])
            wrong_score = next(s for s in scores if test["wrong"] in s["product_name"])
            
            assert right_score["relevance"] > wrong_score["relevance"], \
                f"For '{test['search']}': {test['right']} should outrank {test['wrong']}"

# Performance test
def test_performance():
    """Ensure response time is under 50ms for typical request"""
    import time
    
    products = [{"name": f"Product {i}", "brand": "Test"} for i in range(20)]
    
    start = time.time()
    engine.score_products("test", products)
    elapsed = (time.time() - start) * 1000
    
    assert elapsed < 50, f"Processing took {elapsed}ms, should be under 50ms"

if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v"])

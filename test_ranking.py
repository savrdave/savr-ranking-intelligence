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

# Continue testing many other secnarios:

class TestAllSampleData:
    """Test EVERY scenario in sample_data.json"""
    
    def test_all_sample_scenarios(self):
        """Test all products in sample_data.json meet expected relevance"""
        import json
        
        # Load the sample data
        with open("sample_data.json", "r") as f:
            data = json.load(f)
        
        failed_tests = []
        
        for test_case in data["test_cases"]:
            search_term = test_case["search_term"]
            products = test_case["products"]
            
            # Get scores from engine
            scores = engine.score_products(search_term, products)
            
            # Check each product meets expected relevance
            for product in products:
                expected = product["expected_relevance"]
                
                # Find actual score
                actual_score = next(
                    (s for s in scores if product["name"] in s["product_name"]), 
                    None
                )
                
                if actual_score:
                    actual = actual_score["relevance"]
                    
                    # Allow 0.2 margin of error
                    if abs(actual - expected) > 0.2:
                        failed_tests.append({
                            "search": search_term,
                            "product": product["name"],
                            "expected": expected,
                            "actual": actual,
                            "difference": abs(actual - expected)
                        })
        
        # Report failures
        if failed_tests:
            print("\n❌ FAILED RELEVANCE TESTS:")
            for fail in failed_tests[:10]:  # Show first 10 failures
                print(f"  Search: '{fail['search']}'")
                print(f"  Product: {fail['product']}")
                print(f"  Expected: {fail['expected']}, Got: {fail['actual']}")
                print()
            
            assert False, f"{len(failed_tests)} products scored incorrectly"
        else:
            print(f"\n✅ All {len(data['test_cases'])} test scenarios passed!")

    def test_edge_cases_from_sample(self):
        """Test all edge cases defined in sample_data.json"""
        import json
        
        with open("sample_data.json", "r") as f:
            data = json.load(f)
        
        for edge_case in data["edge_cases"]:
            scenario = edge_case["scenario"]
            search = edge_case["search_term"]
            products = edge_case["products"]
            
            # Convert to format engine expects
            product_list = [{"name": p["name"]} for p in products]
            scores = engine.score_products(search, product_list)
            
            # Check preferred item ranks higher
            preferred = [p for p in products if p.get("prefer", False)]
            not_preferred = [p for p in products if not p.get("prefer", False)]
            
            if preferred and not_preferred:
                pref_score = next(s for s in scores if preferred[0]["name"] in s["product_name"])
                not_pref_score = next(s for s in scores if not_preferred[0]["name"] in s["product_name"])
                
                assert pref_score["relevance"] > not_pref_score["relevance"], \
                    f"Failed {scenario}: {preferred[0]['name']} should rank higher"

    def test_common_mistakes(self):
        """Test that common mistakes from sample_data.json are avoided"""
        import json
        
        with open("sample_data.json", "r") as f:
            data = json.load(f)
        
        # Test each common mistake
        mistake_tests = [
            ("cream", "Heavy Cream 35%", "Ice Cream"),
            ("ham", "Black Forest Ham", "Hamburger Buns"),
            ("rice", "Basmati Rice", "Rice Cakes"),
            ("oil", "Olive Oil", "Essential Oil"),
            ("bread", "Wonder Bread", "Breadcrumbs")
        ]
        
        for search, right, wrong in mistake_tests:
            products = [
                {"name": right},
                {"name": wrong}
            ]
            scores = engine.score_products(search, products)
            
            right_score = next(s for s in scores if right in s["product_name"])
            wrong_score = next(s for s in scores if wrong in s["product_name"])
            
            assert right_score["relevance"] > wrong_score["relevance"], \
                f"Common mistake: '{right}' should rank higher than '{wrong}' for '{search}'"


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

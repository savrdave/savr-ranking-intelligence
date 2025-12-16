# SAVR Ranking Intelligence API

## Project Overview
Build a standalone API that scores grocery product relevance for search terms. This service helps SAVR's main system avoid expensive AI API calls by providing fast, accurate pre-filtering of search results.

## Your Mission
When someone searches for "corn", they want corn on the cob, NOT corn dogs. Your job is to build intelligence that understands this difference.

## Success Criteria
- ✅ Response time: <50ms per request
- ✅ Accuracy: 95%+ confidence when marking products as relevant/irrelevant  
- ✅ Coverage: Handle 60%+ of common grocery searches confidently
- ✅ Cost impact: Each confident response saves $0.001 in AI costs

## Quick Start

### 1. Clone and Setup
```bash
git clone [this-repo-url]
cd savr-ranking-intelligence
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the API
```bash
python main.py
```
The API will start at http://localhost:8001

### 3. Test Your Code
```bash
pytest test_ranking.py -v
```

### 4. Try the API
```bash
curl -X POST "http://localhost:8001/rank" \
  -H "Content-Type: application/json" \
  -d '{
    "search_term": "corn",
    "products": [
      {"name": "Corn on the Cob", "brand": "Fresh"},
      {"name": "Pogo Corn Dogs", "brand": "Pogo"}
    ]
  }'
```

## API Specification

### POST /rank
**Request:**
```json
{
  "search_term": "milk",
  "products": [
    {"name": "2% Milk", "brand": "Neilson", "price": 4.99},
    {"name": "Milk Chocolate Bar", "brand": "Cadbury", "price": 2.99}
  ]
}
```

**Response:**
```json
{
  "scores": [
    {
      "index": 0,
      "relevance": 0.95,
      "confidence": "high",
      "reason": "exact_match",
      "product_name": "2% Milk"
    },
    {
      "index": 1,
      "relevance": 0.15,
      "confidence": "high",
      "reason": "excluded_term",
      "product_name": "Milk Chocolate Bar"
    }
  ],
  "metadata": {
    "model_version": "1.0.0",
    "processing_time_ms": 23,
    "products_analyzed": 2
  }
}
```

## Key Files to Modify

### `ranking_engine.py`
This is where you'll spend 90% of your time. Current implementation is basic - your job is to make it smart.

Key methods to improve:
- `_calculate_relevance()` - Core scoring logic
- `_load_categories()` - Product taxonomy
- `_load_exclusion_patterns()` - Wrong match detection

### `data/` directory (you'll create this)
Build JSON files with:
- Product categories and hierarchies
- Brand name variations  
- Size normalizations
- Common substitutions
- Exclusion patterns

## Development Guidelines

### DO:
- Focus on accuracy first, speed second
- Return high confidence only when >95% sure
- Handle edge cases (bulk vs single, brand variations)
- Test with real product names from grocery stores
- Add comments explaining your logic

### DON'T:
- Try to access SAVR's main system
- Make external API calls (this needs to be fast)
- Store user data or personal information
- Worry about authentication (handled by main system)

## Testing Your Logic

The test file includes common problematic searches:
- "corn" → Should prefer "Corn on Cob" over "Corn Dogs"
- "cream" → Should prefer "Heavy Cream" over "Ice Cream"  
- "butter" → Should prefer "Butter" over "Peanut Butter"

Make all tests pass, then add your own edge cases.

## Performance Requirements
- Handle 20 products in <50ms
- Use minimal memory (<100MB)
- No external dependencies beyond requirements.txt

## Questions?
Focus on building great ranking logic. The integration with SAVR's main system will be handled separately.

## Next Steps
1. Run the existing code and tests
2. Identify why tests fail
3. Improve `_calculate_relevance()` logic
4. Build data files for better intelligence
5. Add more test cases for edge scenarios
6. Achieve 95%+ accuracy on common searches

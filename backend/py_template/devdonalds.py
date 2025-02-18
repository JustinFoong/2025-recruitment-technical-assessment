from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from flask import Flask, request, jsonify
from collections import Counter
import re

# ==== Type Definitions ===========================
@dataclass
class CookbookEntry:
    name: str

@dataclass
class RequiredItem():
    name: str
    quantity: int

@dataclass
class Recipe(CookbookEntry):
    required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
    cook_time: int

# =================================================
app = Flask(__name__)

recipe_store = {}

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
    data = request.get_json()
    recipe_name = data.get('input', '')
    parsed_name = parse_handwriting(recipe_name)
    if parsed_name is None:
        return 'Invalid recipe name', 400
    return jsonify({'msg': parsed_name}), 200

# [TASK 1] =======================================
    """
    Takes in recipeName and formats it to:
    hyphens (`-`) and underscores (`_`) should be replaced with a whitespace
    only contain letters and whitespaces
    the first letter of each word should be capitalised
    only be **one** whitespace between words
    resulting string should have a length of `> 0` characters
    """
    
def parse_handwriting(recipeName: str) -> Optional[str]:
    """Format recipe names according to requirements"""
    
    if not recipeName or not recipeName.strip():
        return None
    
    # replacement of unwanted characters
    processed = recipeName.replace('-', ' ').replace('_', ' ')
    processed = ''.join(char for char in processed if char.isalpha() or char.isspace())
    words = processed.strip().split()
    
    if not words:
        return None
    
    # capitalises the first letter for every word
    words = [word.capitalize() for word in words] 
    return ' '.join(words)

# [TASK 2] =======================================
    """
    Adds stuff to cookbook

    Raises:
        ValueError: _description_
        TypeError: _description_

    Returns:
        _type_: _description_
    """
@app.route('/entry', methods=['POST'])
def create_entry():
    try:
        #check validity
        entry_data = validate_entry_data(request.get_json())
        if not entry_data:
            return {}, 400
        
        # store dat    
        recipe_store[entry_data['raw_name']] = entry_data['entry']
        return {}, 200
        
    except (ValueError, TypeError, KeyError):
        return {}, 400

def validate_entry_data(data: Dict) -> Optional[Dict[str, Any]]:
    if not data or 'type' not in data or 'name' not in data:
        return None
        
    # duplicate check
    if data['name'] in recipe_store:
        return None
        
    # split by type 
    if data['type'] == 'ingredient':
        return process_ingredient(data)
    elif data['type'] == 'recipe':
        return process_recipe(data)
    return None

def process_ingredient(data: Dict) -> Optional[Dict[str, Any]]:
    if not isinstance(data.get('cookTime'), int) or data['cookTime'] < 0:
        return None
        
    return {
        'raw_name': data['name'],
        'entry': Ingredient(
            name=parse_handwriting(data['name']) or data['name'],
            cook_time=data['cookTime']
        )
    }

def process_recipe(data: Dict) -> Optional[Dict[str, Any]]:
    if not isinstance(data.get('requiredItems'), list):
        return None
        
    # Check for unique required items
    seen_items = set()
    required_items = []
    
    for item in data['requiredItems']:
        if not isinstance(item, dict) or 'name' not in item or 'quantity' not in item:
            return None
            
        if not isinstance(item['quantity'], int) or item['quantity'] <= 0:
            return None
            
        if item['name'] in seen_items:
            return None
            
        seen_items.add(item['name'])
        required_items.append(RequiredItem(
            name=item['name'],
            quantity=item['quantity']
        ))
    
    return {
        'raw_name': data['name'],
        'entry': Recipe(
            name=parse_handwriting(data['name']) or data['name'],
            required_items=required_items
        )
    }

# [TASK 3] =======================================
    """
    Generates summary of ingredients required by recipe

    Raises:
        ValueError: _description_
        TypeError: _description_

    Returns:
        _type_: _description_
    """
@app.route('/summary', methods=['GET'])
def summary():
    recipe_name = request.args.get('name')
    
    if not recipe_name or recipe_name not in recipe_store:
        return {}, 400
        
    entry = recipe_store[recipe_name]
    if not isinstance(entry, Recipe):
        return {}, 400
    
    try:
        # Generate summary using iterative approach
        summary_data = calculate_recipe_summary(entry)
        return jsonify(summary_data), 200
    except Exception:
        return {}, 400

def calculate_recipe_summary(recipe: Recipe) -> Dict[str, Any]:
    ingredient_counts = Counter()
    total_cooking_time = 0
    
    # lets use a stack to hold everything
    stack = [(recipe, 1)]
    processed = set()
    
    # Depth-first iterative traversal
    while stack:
        current_entry, multiplier = stack.pop()
        
        if isinstance(current_entry, Ingredient):
            ingredient_counts[current_entry.name] += multiplier
            total_cooking_time += current_entry.cook_time * multiplier
            
        elif isinstance(current_entry, Recipe):
            for req_item in reversed(current_entry.required_items):
                if req_item.name not in recipe_store:
                    raise ValueError(f"Missing item: {req_item.name}")
                    
                # multiply everything 
                new_multiplier = multiplier * req_item.quantity
                required_entry = recipe_store[req_item.name]
                
                # Add to stack
                stack.append((required_entry, new_multiplier))
        else:
            raise TypeError(f"Invalid entry type: {type(current_entry)}")
    
    # Format reponse
    return {
        "name": recipe.name,
        "cookTime": total_cooking_time,
        "ingredients": [
            {"name": name, "quantity": qty}
            for name, qty in sorted(ingredient_counts.items())
        ]
    }

# ==========================================================
if __name__ == '__main__':
    app.run(debug=True, port=8080)
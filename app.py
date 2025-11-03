#!/usr/bin/env python3
"""
Flask Web API for NY SLA Japanese Restaurant Agent
This allows the agent to run as a web service on Render
"""

from flask import Flask, jsonify, request
from datetime import datetime
import json
import sys
import os

# Import the agent
from ny_sla_japanese_restaurants_agent import NYSLAJapaneseRestaurantAgent

app = Flask(__name__)
agent = NYSLAJapaneseRestaurantAgent()

@app.route('/')
def home():
    """Home endpoint with API documentation"""
    return jsonify({
        'name': 'NY SLA Japanese Restaurant Tracker API',
        'version': '1.0.0',
        'description': 'Monitor NY State Liquor Authority for new Japanese restaurant openings',
        'endpoints': {
            '/': 'This documentation',
            '/health': 'Health check',
            '/search': 'Search for Japanese restaurants (GET)',
            '/search/nyc': 'Get NYC borough summary (GET)',
            '/search/county/<county>': 'Search specific county (GET)'
        },
        'parameters': {
            'limit': 'Max records to fetch (default: 10000)',
            'save': 'Save to file (true/false, default: false)'
        },
        'example': '/search?limit=1000&save=false'
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'ny-sla-japanese-restaurant-tracker'
    })

@app.route('/search')
def search_all():
    """Search all of NY State for Japanese restaurants"""
    try:
        limit = request.args.get('limit', 10000, type=int)
        save = request.args.get('save', 'false').lower() == 'true'
        
        # Fetch and filter
        pending = agent.fetch_pending_licenses(limit=limit)
        restaurants = agent.filter_japanese_restaurants(pending)
        
        # Optionally save
        filename = None
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ny_sla_japanese_restaurants_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(restaurants, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'count': len(restaurants),
            'timestamp': datetime.now().isoformat(),
            'filters': {
                'county': 'all',
                'limit': limit
            },
            'saved_to': filename,
            'restaurants': restaurants
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/search/nyc')
def search_nyc():
    """Get NYC borough summary"""
    try:
        limit = request.args.get('limit', 5000, type=int)
        
        results = agent.get_nyc_boroughs_summary()
        
        # Count totals
        summary = {}
        total = 0
        for borough, restaurants in results.items():
            count = len(restaurants)
            summary[borough] = {
                'count': count,
                'restaurants': restaurants
            }
            total += count
        
        return jsonify({
            'success': True,
            'total_count': total,
            'timestamp': datetime.now().isoformat(),
            'boroughs': summary
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/search/county/<county>')
def search_county(county):
    """Search specific county"""
    try:
        limit = request.args.get('limit', 10000, type=int)
        save = request.args.get('save', 'false').lower() == 'true'
        
        # Fetch and filter
        pending = agent.fetch_pending_licenses(limit=limit, county=county)
        restaurants = agent.filter_japanese_restaurants(pending)
        
        # Optionally save
        filename = None
        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{county.lower()}_japanese_restaurants_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(restaurants, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            'success': True,
            'count': len(restaurants),
            'timestamp': datetime.now().isoformat(),
            'filters': {
                'county': county,
                'limit': limit
            },
            'saved_to': filename,
            'restaurants': restaurants
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/search/borough/<borough>')
def search_borough(borough):
    """Search specific NYC borough"""
    # Map borough names to counties
    borough_map = {
        'manhattan': 'New York',
        'brooklyn': 'Kings',
        'queens': 'Queens',
        'bronx': 'Bronx',
        'staten-island': 'Richmond',
        'statenisland': 'Richmond'
    }
    
    county = borough_map.get(borough.lower())
    if not county:
        return jsonify({
            'success': False,
            'error': f'Unknown borough: {borough}. Use manhattan, brooklyn, queens, bronx, or staten-island',
            'timestamp': datetime.now().isoformat()
        }), 400
    
    return search_county(county)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
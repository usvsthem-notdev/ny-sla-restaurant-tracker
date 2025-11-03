#!/usr/bin/env python3
"""
Flask Web API for NY SLA Japanese Restaurant Agent - Standalone Version
All functionality in one file for easy deployment.
"""

from flask import Flask, jsonify, request
from datetime import datetime
import json
import requests
from typing import List, Dict, Optional

app = Flask(__name__)

# Configuration
PENDING_API = "https://data.ny.gov/resource/t5r8-ymc5.json"
JAPANESE_KEYWORDS = [
    'sushi', 'ramen', 'izakaya', 'yakitori', 'tempura',
    'japanese', 'japan', 'tokyo', 'osaka', 'kyoto',
    'teriyaki', 'udon', 'soba', 'bento', 'hibachi',
    'teppanyaki', 'robata', 'omakase', 'sake bar',
    'shochu', 'katsu', 'tonkatsu', 'yakiniku', 'okonomiyaki'
]
RESTAURANT_TYPES = [
    'Restaurant Wine', 'Restaurant/Tavern Wine & Beer',
    'Eating Place Beer', 'Restaurant', 'Tavern Wine',
    'On Premises Liquor', 'Wine, Beer, Cider'
]

def fetch_licenses(limit=10000, county=None):
    params = {'$limit': limit, '$order': 'filing_date DESC'}
    if county:
        params['county'] = county.upper()
    try:
        r = requests.get(PENDING_API, params=params, timeout=30)
        r.raise_for_status()
        return r.json()
    except:
        return []

def is_japanese(record):
    text = ' '.join([str(record.get(f, '')).lower() for f in 
                     ['premises_name', 'doing_business_as_name', 'trade_name']])
    return any(kw in text for kw in JAPANESE_KEYWORDS)

def is_restaurant(record):
    lt = record.get('license_type_description', '').lower()
    return any(rt.lower() in lt for rt in RESTAURANT_TYPES)

def filter_japanese(records):
    return [r for r in records if is_restaurant(r) and is_japanese(r)]

@app.route('/')
def home():
    return jsonify({
        'name': 'NY SLA Japanese Restaurant Tracker API',
        'version': '1.0.0',
        'description': 'Monitor NY State Liquor Authority for new Japanese restaurant openings',
        'endpoints': {
            '/': 'This documentation',
            '/health': 'Health check',
            '/search': 'Search all NY State',
            '/search/nyc': 'NYC borough summary',
            '/search/county/<county>': 'Search specific county',
            '/search/borough/<borough>': 'Search specific borough'
        },
        'example': '/search/borough/manhattan?limit=100'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'ny-sla-japanese-restaurant-tracker'
    })

@app.route('/search')
def search_all():
    try:
        limit = request.args.get('limit', 10000, type=int)
        records = fetch_licenses(limit=limit)
        restaurants = filter_japanese(records)
        return jsonify({
            'success': True,
            'count': len(restaurants),
            'timestamp': datetime.now().isoformat(),
            'restaurants': restaurants
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/search/county/<county>')
def search_county(county):
    try:
        limit = request.args.get('limit', 10000, type=int)
        records = fetch_licenses(limit=limit, county=county)
        restaurants = filter_japanese(records)
        return jsonify({
            'success': True,
            'count': len(restaurants),
            'county': county,
            'timestamp': datetime.now().isoformat(),
            'restaurants': restaurants
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/search/borough/<borough>')
def search_borough(borough):
    boroughs = {
        'manhattan': 'New York',
        'brooklyn': 'Kings',
        'queens': 'Queens',
        'bronx': 'Bronx',
        'staten-island': 'Richmond',
        'statenisland': 'Richmond'
    }
    county = boroughs.get(borough.lower())
    if not county:
        return jsonify({
            'success': False,
            'error': f'Unknown borough: {borough}. Use manhattan, brooklyn, queens, bronx, or staten-island'
        }), 400
    return search_county(county)

@app.route('/search/nyc')
def search_nyc():
    try:
        boroughs = {
            'Manhattan': 'New York',
            'Brooklyn': 'Kings',
            'Queens': 'Queens',
            'Bronx': 'Bronx',
            'Staten Island': 'Richmond'
        }
        summary = {}
        total = 0
        for borough, county in boroughs.items():
            records = fetch_licenses(county=county, limit=5000)
            restaurants = filter_japanese(records)
            summary[borough] = {
                'count': len(restaurants),
                'restaurants': restaurants
            }
            total += len(restaurants)
        return jsonify({
            'success': True,
            'total_count': total,
            'timestamp': datetime.now().isoformat(),
            'boroughs': summary
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
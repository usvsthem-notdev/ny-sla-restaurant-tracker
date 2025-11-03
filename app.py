#!/usr/bin/env python3
"""
Flask Web API for NY SLA Japanese Restaurant Agent - Debug Version
All functionality in one file with comprehensive debugging.
"""

from flask import Flask, jsonify, request
from datetime import datetime
import json
import requests
from typing import List, Dict, Optional
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PENDING_API = "https://data.ny.gov/resource/t5r8-ymc5.json"
ACTIVE_API = "https://data.ny.gov/resource/9s3h-dpkz.json"
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

def fetch_licenses(limit=10000, county=None, use_active=False):
    """Fetch licenses from NY SLA API with debugging"""
    api_url = ACTIVE_API if use_active else PENDING_API
    params = {'$limit': limit, '$order': 'filing_date DESC'}
    if county:
        params['county'] = county.upper()
    
    logger.info(f"Fetching from {api_url} with params: {params}")
    
    try:
        r = requests.get(api_url, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        logger.info(f"Successfully fetched {len(data)} records from SLA API")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching from SLA API: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return []

def is_japanese(record):
    """Check if record matches Japanese keywords"""
    text = ' '.join([str(record.get(f, '')).lower() for f in 
                     ['premises_name', 'doing_business_as_name', 'trade_name']])
    matches = [kw for kw in JAPANESE_KEYWORDS if kw in text]
    return len(matches) > 0, matches

def is_restaurant(record):
    """Check if record is a restaurant type license"""
    lt = record.get('license_type_description', '').lower()
    matches = [rt for rt in RESTAURANT_TYPES if rt.lower() in lt]
    return len(matches) > 0, matches

def filter_japanese(records):
    """Filter for Japanese restaurants with detailed logging"""
    japanese_restaurants = []
    restaurant_count = 0
    japanese_count = 0
    
    for r in records:
        is_rest, rest_matches = is_restaurant(r)
        is_jap, jap_matches = is_japanese(r)
        
        if is_rest:
            restaurant_count += 1
        if is_jap:
            japanese_count += 1
            
        if is_rest and is_jap:
            r['_debug_matched_keywords'] = jap_matches
            r['_debug_matched_types'] = rest_matches
            japanese_restaurants.append(r)
    
    logger.info(f"Filtered {len(records)} records: {restaurant_count} restaurants, "
                f"{japanese_count} Japanese, {len(japanese_restaurants)} Japanese restaurants")
    
    return japanese_restaurants

@app.route('/')
def home():
    return jsonify({
        'name': 'NY SLA Japanese Restaurant Tracker API',
        'version': '2.0.0-debug',
        'description': 'Monitor NY State Liquor Authority for new Japanese restaurant openings',
        'endpoints': {
            '/': 'This documentation',
            '/health': 'Health check',
            '/debug': 'Diagnostic information and raw data samples',
            '/debug/test-api': 'Test direct connection to SLA API',
            '/debug/sample': 'Get sample records from SLA API',
            '/debug/stats': 'Get statistics about current data',
            '/search': 'Search all NY State',
            '/search/nyc': 'NYC borough summary',
            '/search/county/<county>': 'Search specific county',
            '/search/borough/<borough>': 'Search specific borough'
        },
        'example': '/search/borough/manhattan?limit=100',
        'debug_examples': '/debug/sample?limit=10'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'ny-sla-japanese-restaurant-tracker',
        'version': '2.0.0-debug'
    })

@app.route('/debug')
def debug_info():
    """Comprehensive diagnostic endpoint"""
    return jsonify({
        'endpoints': {
            'pending_api': PENDING_API,
            'active_api': ACTIVE_API
        },
        'filters': {
            'japanese_keywords': JAPANESE_KEYWORDS,
            'restaurant_types': RESTAURANT_TYPES
        },
        'test_endpoints': {
            '/debug/test-api': 'Test SLA API connection',
            '/debug/sample': 'View raw SLA data samples',
            '/debug/stats': 'Get filtering statistics'
        },
        'usage': {
            'test_connection': 'GET /debug/test-api',
            'see_raw_data': 'GET /debug/sample?limit=10',
            'see_stats': 'GET /debug/stats?county=New%20York'
        }
    })

@app.route('/debug/test-api')
def debug_test_api():
    """Test direct connection to both SLA APIs"""
    results = {}
    
    # Test pending API
    try:
        logger.info("Testing PENDING API connection...")
        r = requests.get(f"{PENDING_API}?$limit=1", timeout=10)
        r.raise_for_status()
        results['pending_api'] = {
            'status': 'success',
            'status_code': r.status_code,
            'url': PENDING_API,
            'record_count': len(r.json()),
            'sample': r.json()[0] if r.json() else None
        }
    except Exception as e:
        results['pending_api'] = {
            'status': 'error',
            'error': str(e),
            'url': PENDING_API
        }
    
    # Test active API
    try:
        logger.info("Testing ACTIVE API connection...")
        r = requests.get(f"{ACTIVE_API}?$limit=1", timeout=10)
        r.raise_for_status()
        results['active_api'] = {
            'status': 'success',
            'status_code': r.status_code,
            'url': ACTIVE_API,
            'record_count': len(r.json()),
            'sample': r.json()[0] if r.json() else None
        }
    except Exception as e:
        results['active_api'] = {
            'status': 'error',
            'error': str(e),
            'url': ACTIVE_API
        }
    
    return jsonify(results)

@app.route('/debug/sample')
def debug_sample():
    """Get sample records from SLA API"""
    limit = request.args.get('limit', 10, type=int)
    county = request.args.get('county', None)
    use_active = request.args.get('active', 'false').lower() == 'true'
    
    records = fetch_licenses(limit=limit, county=county, use_active=use_active)
    
    # Add debug info to each record
    for r in records:
        is_rest, rest_matches = is_restaurant(r)
        is_jap, jap_matches = is_japanese(r)
        r['_debug'] = {
            'is_restaurant': is_rest,
            'restaurant_matches': rest_matches,
            'is_japanese': is_jap,
            'japanese_matches': jap_matches
        }
    
    return jsonify({
        'success': True,
        'api_used': ACTIVE_API if use_active else PENDING_API,
        'county': county,
        'total_fetched': len(records),
        'records': records
    })

@app.route('/debug/stats')
def debug_stats():
    """Get detailed statistics about data filtering"""
    limit = request.args.get('limit', 1000, type=int)
    county = request.args.get('county', None)
    use_active = request.args.get('active', 'false').lower() == 'true'
    
    records = fetch_licenses(limit=limit, county=county, use_active=use_active)
    
    stats = {
        'total_records': len(records),
        'restaurants': 0,
        'japanese_text': 0,
        'japanese_restaurants': 0,
        'license_types': {},
        'sample_names': []
    }
    
    for r in records:
        is_rest, rest_matches = is_restaurant(r)
        is_jap, jap_matches = is_japanese(r)
        
        if is_rest:
            stats['restaurants'] += 1
        if is_jap:
            stats['japanese_text'] += 1
        if is_rest and is_jap:
            stats['japanese_restaurants'] += 1
            stats['sample_names'].append({
                'name': r.get('premises_name', 'N/A'),
                'dba': r.get('doing_business_as_name', 'N/A'),
                'county': r.get('county', 'N/A'),
                'matched_keywords': jap_matches
            })
        
        # Count license types
        lt = r.get('license_type_description', 'Unknown')
        stats['license_types'][lt] = stats['license_types'].get(lt, 0) + 1
    
    stats['sample_names'] = stats['sample_names'][:10]  # Limit to 10 samples
    
    return jsonify({
        'success': True,
        'api_used': ACTIVE_API if use_active else PENDING_API,
        'county': county,
        'statistics': stats
    })

@app.route('/search')
def search_all():
    try:
        limit = request.args.get('limit', 10000, type=int)
        use_active = request.args.get('active', 'false').lower() == 'true'
        records = fetch_licenses(limit=limit, use_active=use_active)
        restaurants = filter_japanese(records)
        return jsonify({
            'success': True,
            'count': len(restaurants),
            'total_records_fetched': len(records),
            'api_used': 'active' if use_active else 'pending',
            'timestamp': datetime.now().isoformat(),
            'restaurants': restaurants
        })
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/search/county/<county>')
def search_county(county):
    try:
        limit = request.args.get('limit', 10000, type=int)
        use_active = request.args.get('active', 'false').lower() == 'true'
        records = fetch_licenses(limit=limit, county=county, use_active=use_active)
        restaurants = filter_japanese(records)
        return jsonify({
            'success': True,
            'count': len(restaurants),
            'total_records_fetched': len(records),
            'county': county,
            'api_used': 'active' if use_active else 'pending',
            'timestamp': datetime.now().isoformat(),
            'restaurants': restaurants
        })
    except Exception as e:
        logger.error(f"County search error: {str(e)}")
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
        use_active = request.args.get('active', 'false').lower() == 'true'
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
            records = fetch_licenses(county=county, limit=5000, use_active=use_active)
            restaurants = filter_japanese(records)
            summary[borough] = {
                'count': len(restaurants),
                'total_fetched': len(records),
                'restaurants': restaurants
            }
            total += len(restaurants)
        return jsonify({
            'success': True,
            'total_count': total,
            'api_used': 'active' if use_active else 'pending',
            'timestamp': datetime.now().isoformat(),
            'boroughs': summary
        })
    except Exception as e:
        logger.error(f"NYC search error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

# NY SLA Japanese Restaurant Opening Tracker

An automated agent that monitors the New York State Liquor Authority (SLA) open data API to identify new Japanese restaurant openings across New York State.

## Features

- **Real-time Monitoring**: Fetches the latest pending liquor license applications from NY SLA
- **Intelligent Filtering**: Identifies Japanese restaurants using comprehensive keyword matching
- **Geographic Filtering**: Search by county or NYC borough
- **Web API**: Flask-based REST API for easy integration
- **Cloud-Ready**: Configured for deployment on Render

## Quick Start

### Local Development

```bash
pip install -r requirements.txt
python3 app.py
```

Access the API at: http://localhost:5000

### Deploy to Render

This repository is configured for one-click deployment to Render.

## API Endpoints

- `GET /` - API documentation
- `GET /health` - Health check
- `GET /search` - Search all of NY State
- `GET /search/nyc` - Get NYC borough summary
- `GET /search/county/<county>` - Search specific county
- `GET /search/borough/<borough>` - Search specific borough

## Example Usage

```bash
# Health check
curl https://your-service.onrender.com/health

# Search Manhattan
curl https://your-service.onrender.com/search/borough/manhattan

# NYC Summary
curl https://your-service.onrender.com/search/nyc
```

## Data Source

- **Pending Licenses**: https://data.ny.gov/resource/t5r8-ymc5.json
- **Active Licenses**: https://data.ny.gov/resource/9s3h-dpkz.json

Data is updated daily by the NY State Liquor Authority.

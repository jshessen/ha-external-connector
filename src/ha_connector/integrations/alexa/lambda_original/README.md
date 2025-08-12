# Original Lambda Functions Reference

This directory contains the original working Lambda function code from dkaser's GitHub gist, used as a reference for comparison and debugging.

## Files

### `Home_Assistant_original.py`

- **Purpose**: Original Smart Home Bridge Lambda function
- **Equivalent to**: `smart_home_bridge.py` in our current implementation
- **Function**: Processes Alexa Smart Home directives and forwards them to Home Assistant
- **Source**: <https://gist.githubusercontent.com/dkaser/bcfc82c4f84ef02c81c218f36afdca01/raw/5a196cf683e991789111434ddedfcfc6de8ff9b2/Home_Assistant.py>

### `Home_Assistant_Wrapper_original.py`

- **Purpose**: Original OAuth Gateway Lambda function
- **Equivalent to**: `oauth_gateway.py` in our current implementation
- **Function**: Handles OAuth authentication flow and token exchanges
- **Source**: <https://gist.githubusercontent.com/dkaser/bcfc82c4f84ef02c81c218f36afdca01/raw/5a196cf683e991789111434ddedfcfc6de8ff9b2/Home_Assistant_Wrapper.py>

## Key Original Patterns

### Authentication Headers

- Always includes CloudFlare Access headers regardless of content
- Uses `.format()` string formatting for headers
- No conditional logic for CloudFlare credential inclusion

### Token Extraction

- Multi-location search: endpoint.scope → payload.grantee → payload.scope
- Debug fallback to HA_TOKEN only when debug mode enabled
- Uses assert statements for validation

### Request Configuration

- urllib3.PoolManager with specific timeout settings
- SSL verification based on NOT_VERIFY_SSL environment variable
- Direct JSON encoding: `json.dumps(event).encode('utf-8')`

## Usage for Debugging

These files serve as the **authoritative reference** for:

1. **Comparing authentication patterns** - CloudFlare header handling
2. **Analyzing token extraction logic** - Original multi-location search
3. **Verifying request formatting** - Exact urllib3 configuration
4. **Understanding error handling** - Original assertion-based validation

When troubleshooting authentication issues, compare our current implementation against these proven working patterns.

## Download Date

Downloaded: August 11, 2025

## Original Author

Copyright 2019 Jason Hu &lt;awaregit at gmail.com&gt;
Licensed under the Apache License, Version 2.0

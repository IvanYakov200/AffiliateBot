import requests
from config.config import APPSFLYER_API_KEY, APPSFLYER_APP_ID, APPSFLYER_BASE_URL, logger

def get_appsflyer_raw_data_custom(endpoint: str, params: dict) -> bytes:
    """Get raw data from AppsFlyer API"""
    headers = {
        "Authorization": f"Bearer {APPSFLYER_API_KEY}",
        "Accept": "text/csv"
    }

    # Default parameters
    default_params = {
        'app_id': APPSFLYER_APP_ID,
        'timezone': 'Europe/Moscow'
    }
    params.update(default_params)

    try:
        logger.info(f"Sending request to: {endpoint}")
        logger.info(f"Parameters: {params}")

        response = requests.get(endpoint, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.content

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        raise

def get_post_attribution_report(params: dict) -> bytes:
    """Get post-attribution report from AppsFlyer"""
    endpoint = f"{APPSFLYER_BASE_URL}/{params['app_id']}/fraud-post-inapps/v5"
    headers = {
        "Authorization": f"Bearer {APPSFLYER_API_KEY}",
        "Accept": "text/csv"
    }
    
    # Добавляем параметры по умолчанию
    default_params = {
        'timezone': 'Europe/Moscow'
    }
    params.update(default_params)
    
    try:
        logger.info(f"Sending post-attribution request to: {endpoint}")
        logger.info(f"Parameters: {params}")
        logger.info(f"Headers: {headers}")
        
        response = requests.get(endpoint, headers=headers, params=params, timeout=30)
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        response.raise_for_status()
        
        if not response.content:
            logger.warning("Empty response received from post-attribution endpoint")
            return None
            
        logger.info(f"Response content length: {len(response.content)} bytes")
        return response.content
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Post-attribution request error: {str(e)}")
        if hasattr(e.response, 'text'):
            logger.error(f"Error response: {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in post-attribution: {str(e)}")
        raise

def add_offer_filter(params: dict, offer_id: str) -> dict:
    """Add filters for specific offer and additional fields"""
    params.update({
        'event_name': f'offer_{offer_id}',
        'additional_fields': ','.join([
            'blocked_reason_rule', 'store_reinstall', 'impressions',
            'contributor3_match_type', 'custom_dimension', 'conversion_type',
            'gp_click_time', 'match_type', 'mediation_network', 'oaid',
            'deeplink_url', 'blocked_reason', 'blocked_sub_reason',
            'gp_broadcast_referrer', 'gp_install_begin', 'campaign_type',
            'custom_data', 'rejected_reason', 'device_download_time',
            'keyword_match_type', 'contributor1_match_type',
            'contributor2_match_type', 'device_model', 'monetization_network',
            'segment', 'is_lat', 'gp_referrer', 'blocked_reason_value',
            'store_product_page', 'device_category', 'app_type',
            'rejected_reason_value', 'ad_unit', 'keyword_id', 'placement',
            'network_account_id', 'install_app_store', 'amazon_aid', 'att',
            'engagement_type', 'gdpr_applies', 'ad_user_data_enabled',
            'ad_personalization_enabled'
        ])
    })
    return params 
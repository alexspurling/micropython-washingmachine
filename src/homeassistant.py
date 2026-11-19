"""Report battery data to Home Assistant.

Discovers Home Assistant on the local network via mDNS (zero-config, just
like airlytix devices).  If that fails, falls back to secrets.HA_URL if set.
"""
from microWebCli import MicroWebCli
import secrets
import mdns


# Entity IDs
_BATTERY_SENSOR = 'sensor.wakeboard_battery'
_WASH_EVENT = 'event.wakeboard_wash'


_DISCOVERED = None  # cached (hostname, ip, port)


def _discover_ha():
    global _DISCOVERED
    if _DISCOVERED is not None:
        return _DISCOVERED

    print('Discovering Home Assistant via mDNS...')
    result = mdns.discover(timeout_sec=3)
    if result:
        hostname, ip, port = result
        url = 'http://{}:{}'.format(ip, port)
        print('Discovered HA at', url)
        _DISCOVERED = (hostname, ip, port)
        return result

    # Fall back to configured URL
    url = getattr(secrets, 'HA_URL', None)
    if url:
        print('Using configured HA_URL:', url)
        _DISCOVERED = (None, None, None)  # prevent re-try
        return (None, url, None)

    print('No Home Assistant found (mDNS failed, HA_URL not set)')
    _DISCOVERED = (None, None, None)
    return None


def report_battery(battery_percentage, battery_voltage):
    """Report battery level to Home Assistant via REST API.

    Returns True on success, False if HA is not reachable or not configured.
    """
    discovered = _discover_ha()
    if discovered is None:
        return False

    hostname, ip_or_url, port = discovered

    if hostname is None and ip_or_url:
        # Fallback from configured HA_URL
        url = '{}/api/states/{}'.format(ip_or_url, _BATTERY_SENSOR)
    else:
        url = 'http://{}:{}/api/states/{}'.format(
            ip_or_url, port, _BATTERY_SENSOR)

    data = {
        'state': '{:.1f}'.format(battery_percentage),
        'attributes': {
            'unit_of_measurement': '%',
            'friendly_name': 'Wakeboard Battery',
            'battery_voltage': round(battery_voltage, 2),
            'device_class': 'battery',
        },
    }

    # Use Bearer token if configured
    auth = None
    token = getattr(secrets, 'HA_TOKEN', None)
    if token:
        auth = MicroWebCli.AuthToken(token)

    try:
        result = MicroWebCli.JSONRequest(url, data, auth=auth)
    except Exception as e:
        print('HA request failed:', e)
        return False

    if result is None:
        print('HA battery report failed (no response)')
        return False

    print('Battery reported to Home Assistant: {:.1f}% ({:.2f}V)'.format(
        battery_percentage, battery_voltage))
    return True

def report_wash_event():
    """Record a wash cycle completion in Home Assistant.

    Fires a Home Assistant event called wakeboard_wash.
    Home Assistant records the event with its own timestamp.
    No counter, NTP or timer required.
    """
    discovered = _discover_ha()
    if discovered is None:
        return False

    hostname, ip_or_url, port = discovered

    if hostname is None and ip_or_url:
        url = '{}/api/events/wakeboard_wash'.format(ip_or_url)
    else:
        url = 'http://{}:{}/api/events/wakeboard_wash'.format(
            ip_or_url, port
        )

    data = {
        'event_type': 'wash_cycle_completed',
    }

    auth = None
    token = getattr(secrets, 'HA_TOKEN', None)
    if token:
        auth = MicroWebCli.AuthToken(token)

    try:
        result = MicroWebCli.JSONRequest(url, data, auth=auth)
    except Exception as e:
        print('HA wash event request failed:', e)
        return False

    if result is None:
        print('HA wash event failed (no response)')
        return False

    print('Wash event recorded')
    return True
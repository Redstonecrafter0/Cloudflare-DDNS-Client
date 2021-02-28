import json
import logging
import pathlib
import requests
from time import sleep

loggingformatter = logging.Formatter('[%(asctime)s] [%(levelname)s] : %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(loggingformatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)
logsPath = pathlib.Path('logs')
if not logsPath.exists() or not logsPath.is_dir():
    logsPath.mkdir()
logFile = pathlib.Path('logs/latest.log')
try:
    logFile.unlink()
except FileNotFoundError:
    pass
except:
    logger.exception('Error in log file')
handler = logging.FileHandler('logs/latest.log')
handler.setFormatter(loggingformatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)

base_url = 'https://api.cloudflare.com/client/v4/'

with open('config.json') as f:
    config = json.loads(f.read())

while True:
    try:
        last_ip = requests.get('http://checkip.dyndns.org').text.split('<body>Current IP Address: ')[1].split('</body>')[0]
        if config['last_ip'] != last_ip:
            config['last_ip'] = last_ip
            with open('config.json', 'w') as f:
                f.write(json.dumps(config, indent=2))
            t = requests.get(f'{base_url}zones/{config["zone_id"]}/dns_records', headers={'Authorization': f'Bearer {config["api_key"]}'}).json()
            domains = [(i['id'], i['name'], i['ttl'], i['proxied']) for i in t['result'] if i['type'] == 'A' and i['name'] in config['subdomains'] and i['content'] != config['last_ip']]
            for domain_id, subdomain, ttl, proxied in domains:
                requests.put(f'{base_url}zones/{config["zone_id"]}/dns_records/{domain_id}', data=json.dumps({
                    'type': 'A',
                    'name': subdomain,
                    'content': config['last_ip'],
                    'ttl': ttl,
                    'proxied': proxied
                }), headers={'Authorization': f'Bearer {config["api_key"]}'})
                logger.info(f'Updated {subdomain} to {config["last_ip"]}')
    except Exception as e:
        logger.exception(e)
    sleep(10 * 60)

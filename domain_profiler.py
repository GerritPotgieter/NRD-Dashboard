import requests
import time
import json
import os
import datetime
import re
import csv
from dotenv import load_dotenv

load_dotenv()
# Use repo root Output folder (domain_profiler.py is in the root directory)
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
output_dir = os.path.join(ROOT_DIR, "Output", "Domain_Profiles")
os.makedirs(output_dir, exist_ok=True)

# === API Keys ===
API_KEYS = {
    "viewdns": os.getenv("VIEW_DNS_API_KEY"),
    "virustotal": os.getenv("VIRUS_TOTAL_API_KEY"),
    "securitytrails": os.getenv("SECURITY_TRAILS_API_KEY"),
    "dnsdumpster": os.getenv("DNS_DUMPSTER_API_KEY")
}

# === ViewDNS Functions ===
def viewdns_propCheck(domain):
    """Fetch WHOIS info from ViewDNS."""
    print(f"[ViewDNS] WHOIS lookup for: {domain}")
    api_url = f'https://api.viewdns.info/propagation/?domain={domain}&apikey={API_KEYS["viewdns"]}&output=json'
    response = requests.get(api_url)

    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
    return {}

    
def viewdns_reverse_ip(domain):
    """Fetch reverse IP info from ViewDNS."""
    api_url = f'https://api.viewdns.info/reversewhois/?q={domain}&apikey={API_KEYS["viewdns"]}&output=json'

    response = requests.get(api_url)

    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
    return {}

def viewdns_whois(domain):
    """Fetch reverse IP info from ViewDNS."""
    api_url = f'https://api.viewdns.info/whois/v2/?domain={domain}&apikey={API_KEYS["viewdns"]}&output=json'

    response = requests.get(api_url)

    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
    return {}

# === VirusTotal Functions ===
def virustotal_report(domain):
    """Fetch report from VirusTotal."""
    url = f"https://www.virustotal.com/api/v3/domains/{domain}"

    headers = {
        "accept": "application/json",
        "x-apikey": API_KEYS["virustotal"]
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
    return {}
    

def virustotal_related_ips(domain):
    """Fetch related IPs or resolutions from VirusTotal."""
    api_url = f"https://www.virustotal.com/api/v3/domains/{domain}/related_ips"

    headers = {
        "accept": "application/json",
        "x-apikey": API_KEYS["virustotal"]
    }

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
    return {}

# === SecurityTrails Functions ===
def securitytrails_subdomains(domain):
    """Fetch subdomains from SecurityTrails."""
    url = f"https://api.securitytrails.com/v1/domain/{domain}/subdomains?apikey={API_KEYS['securitytrails']}"

    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
    return {}

def securitytrails_whois_history(domain):
    """Fetch WHOIS history from SecurityTrails."""
    url = f"https://api.securitytrails.com/v1/history/{domain}/whois?apikey={API_KEYS['securitytrails']}"

    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
    return {}

def securitytrails_whois(domain):
    """Fetch WHOIS information from SecurityTrails."""
    url = f"https://api.securitytrails.com/v1/domain/{domain}/whois?apikey={API_KEYS['securitytrails']}"

    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
    return {}


def securitytrails_domain(domain):
    """Fetch WHOIS information from SecurityTrails."""
    url = f"https://api.securitytrails.com/v1/domain/{domain}?apikey={API_KEYS['securitytrails']}"

    headers = {"accept": "application/json"}

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code}, {response.text}")
    return {}



#DNS Dumpster Functions
def dnsdumpster(domain):
    """Fetch DNS data from DNSDumpster."""
    api_key = API_KEYS.get("dnsdumpster")
    if not api_key:
        print("Error: DNS_DUMPSTER_API_KEY not set.")
        return {}
    url = f"https://api.dnsdumpster.com/domain/{domain}"
    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json",
        "User-Agent": "NRD-Phishing/1.0"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            print(data)
            return data
        else:
            print(f"[DNSDumpster] Error: {resp.status_code}, {resp.text}")
            return {}
    except requests.RequestException as e:
        print(f"[DNSDumpster] Request failed: {e}")
        return {}



# === Summary Generation ===
def generate_summary(domain, data):
    """Generate a security-focused summary of the domain profile."""
    summary = {
        "domain": domain,
        "risk_indicators": [],
        "subdomains": [],
        "alternative_names": [],
        "security_analysis": {
            "total_engines": 0,
            "flagged_as_malicious": 0,
            "flagged_as_suspicious": 0,
            "clean_ratings": 0,
            "unrated": 0
        },
        "infrastructure": {
            "ip_addresses": [],
            "nameservers": [],
            "hosting_provider": None
        },
        "certificate_info": {
            "has_ssl": False,
            "issuer": None,
            "valid_from": None,
            "alternative_names": []
        },
        "creation_date": None,
        "expiry_date": None
    }
    
    # Extract subdomains from SecurityTrails
    if "securitytrails" in data and "subdomains" in data["securitytrails"]:
        summary["subdomains"] = data["securitytrails"]["subdomains"][:10]  # Limit to first 10
    
    # Extract security analysis from VirusTotal
    if "virustotal" in data and "data" in data["virustotal"]:
        vt_data = data["virustotal"]["data"]
        
        if "attributes" in vt_data:
            attrs = vt_data["attributes"]
            # WHOIS parsing
            if "whois" in attrs and attrs["whois"]:
                raw_whois = attrs["whois"]
                summary["whois_raw"] = raw_whois
                summary.update(parse_whois_into_summary(raw_whois))

            # Security stats
            if "last_analysis_stats" in attrs:
                stats = attrs["last_analysis_stats"]
                summary["security_analysis"]["total_engines"] = sum(stats.values())
                summary["security_analysis"]["flagged_as_malicious"] = stats.get("malicious", 0)
                summary["security_analysis"]["flagged_as_suspicious"] = stats.get("suspicious", 0)
                summary["security_analysis"]["clean_ratings"] = stats.get("harmless", 0)
                summary["security_analysis"]["unrated"] = stats.get("undetected", 0)
            
            # Certificate info
            if "last_https_certificate" in attrs:
                cert = attrs["last_https_certificate"]
                summary["certificate_info"]["has_ssl"] = True
                if "issuer" in cert and "CN" in cert["issuer"]:
                    summary["certificate_info"]["issuer"] = cert["issuer"]["CN"]
                if "validity" in cert and "not_before" in cert["validity"]:
                    summary["certificate_info"]["valid_from"] = cert["validity"]["not_before"]
                if "extensions" in cert and "subject_alternative_name" in cert["extensions"]:
                    summary["certificate_info"]["alternative_names"] = cert["extensions"]["subject_alternative_name"]
            
            # Domain dates
            if "creation_date" in attrs:
                # Convert the date to a readable format
                if isinstance(attrs["creation_date"], int):
                    # Convert Unix timestamp to readable date
                    creation_timestamp = attrs["creation_date"]
                    summary["creation_date"] = datetime.datetime.fromtimestamp(creation_timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')
                else:
                    summary["creation_date"] = attrs["creation_date"]
                
            
            # Extract IPs from DNS records
            if "last_dns_records" in attrs:
                for record in attrs["last_dns_records"]:
                    if record.get("type") == "A":
                        summary["infrastructure"]["ip_addresses"].append(record.get("value"))
                    elif record.get("type") == "NS":
                        summary["infrastructure"]["nameservers"].append(record.get("value"))
    
    # Extract additional IPs from DNSDumpster
    if "dnsdumpster" in data:
        dd_data = data["dnsdumpster"]
        if "a" in dd_data:
            for a_record in dd_data["a"]:
                if "ips" in a_record:
                    for ip_info in a_record["ips"]:
                        if "ip" in ip_info:
                            summary["infrastructure"]["ip_addresses"].append(ip_info["ip"])
                        if "provider" in ip_info:
                            summary["infrastructure"]["hosting_provider"] = ip_info["provider"]
    
    # Generate risk indicators
    risk_indicators = []
    
    # Check for suspicious patterns
    if "absa" in domain.lower():
        risk_indicators.append("Contains 'absa' - potential brand impersonation")
    
    if summary["security_analysis"]["flagged_as_malicious"] > 0:
        risk_indicators.append(f"Flagged as malicious by {summary['security_analysis']['flagged_as_malicious']} security engines")
    
    if summary["security_analysis"]["flagged_as_suspicious"] > 0:
        risk_indicators.append(f"Flagged as suspicious by {summary['security_analysis']['flagged_as_suspicious']} security engines")
    
    # Check for recently created domains
    if summary["creation_date"]:
        try:
            # Parse the formatted date string back to datetime for comparison
            if isinstance(summary["creation_date"], str) and "UTC" in summary["creation_date"]:
                created_str = summary["creation_date"].replace(" UTC", "")
                created = datetime.datetime.strptime(created_str, '%Y-%m-%d %H:%M:%S')
                now = datetime.datetime.now()
                days_old = (now - created).days
                if days_old < 30:
                    risk_indicators.append(f"Recently created domain ({days_old} days old)")
        except Exception as e:
            # If date parsing fails, skip this check
            pass
    
    # Check for suspicious subdomains
    suspicious_subdomains = ["login", "secure", "account", "banking", "portal", "admin"]
    found_suspicious = [sub for sub in summary["subdomains"] if any(sus in sub.lower() for sus in suspicious_subdomains)]
    if found_suspicious:
        risk_indicators.append(f"Suspicious subdomains found: {', '.join(found_suspicious[:3])}")
    
    summary["risk_indicators"] = risk_indicators
    
    # Remove duplicates and clean up
    summary["infrastructure"]["ip_addresses"] = list(set(summary["infrastructure"]["ip_addresses"]))
    summary["infrastructure"]["nameservers"] = list(set(summary["infrastructure"]["nameservers"]))
    
    return summary


# === WHOIS Parsing Helpers ===
WHOIS_FIELD_MAP = {
    r'^domain name': 'domain_name',
    r'^registry domain id': 'registry_domain_id',
    r'^registrar url': 'registrar_url',
    r'^domain registrar url': 'registrar_url',
    r'^updated date': 'updated_date',
    r'^update date': 'updated_date',
    r'^creation date': 'creation_date',
    r'^create date': 'creation_date',
    r'^registry expiry date': 'registry_expiry_date',
    r'^expiry date': 'registry_expiry_date',
    r'^registrar registration expiration date': 'registrar_expiration_date',
    r'^registrar:?$': 'registrar_name',
    r'^registrar iana id': 'registrar_iana_id',
    r'^domain registrar id': 'registrar_iana_id',
    r'^registrar abuse contact email': 'registrar_abuse_email',
    r'^registrar abuse contact phone': 'registrar_abuse_phone',
    r'^dnssec': 'dnssec'
}

CONTACT_SECTION_PREFIXES = {
    'registry registrant id': 'registrant',
    'registrant ': 'registrant',
    'registry admin id': 'admin',
    'admin ': 'admin',
    'administrative ': 'admin',
    'registry tech id': 'tech',
    'tech ': 'tech',
    'technical ': 'tech',
    'registry billing id': 'billing',
    'billing ': 'billing'
}

DATE_KEYS = {
    'creation_date', 'updated_date', 'registry_expiry_date', 'registrar_expiration_date'
}

DATE_INPUT_FORMATS = [
    '%Y-%m-%dT%H:%M:%SZ',
    '%Y-%m-%d %H:%M:%SZ',
    '%Y-%m-%dT%H:%M:%S',
    '%Y-%m-%d %H:%M:%S'
]

def parse_date_to_iso(val):
    for fmt in DATE_INPUT_FORMATS:
        try:
            dt = datetime.datetime.strptime(val, fmt)
            return dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        except Exception:
            continue
    return val  # fallback

def parse_whois_into_summary(raw_whois: str):
    """Parse WHOIS raw text into structured pieces to enrich summary.

    Returns a dict with keys: registrar (nested), domain_dates, registrar_status, registrar_name_servers.
    """
    result = {
        'registrar': {
            'name': None,
            'iana_id': None,
            'url': None,
            'abuse_email': None,
            'abuse_phone': None
        },
        'whois': {},
        'whois_status': [],
        'whois_name_servers': []
    }

    contacts = {
        'registrant': {},
        'admin': {},
        'tech': {},
        'billing': {}
    }

    lines = [l.strip() for l in raw_whois.splitlines() if l.strip()]
    for line in lines:
        # Split on first colon only
        if ':' in line:
            key_part, val_part = line.split(':', 1)
            key = key_part.strip().lower()
            val = val_part.strip()
        else:
            key = line.lower().strip()
            val = ''

        # Capture domain status (can appear multiple times)
        if key.startswith('domain status'):
            # Domain Status: clientDeleteProhibited <url>
            status_token = val.split()[0] if val else ''
            if status_token and status_token not in result['whois_status']:
                result['whois_status'].append(status_token)
            continue

        # Name Server lines
        if key.startswith('name server'):
            ns_val = val.split()[0].lower() if val else ''
            if ns_val and ns_val not in result['whois_name_servers']:
                result['whois_name_servers'].append(ns_val)
            continue

        # Contact section detection
        for prefix, section in CONTACT_SECTION_PREFIXES.items():
            if key.startswith(prefix):
                # Example: Admin City: X  -> key after section prefix
                remainder = key[len(prefix):].strip()
                if not remainder:  # lines like 'Registry Admin ID'
                    contacts[section]['id'] = val
                else:
                    # Map e.g. city/state/country/organization/postal code
                    remainder_clean = remainder.replace(' ', '_')
                    contacts[section][remainder_clean] = val
                break

        # Generic mapped fields
        for pattern, canonical in WHOIS_FIELD_MAP.items():
            if re.match(pattern, key):
                result['whois'][canonical] = val
                break

    # Populate registrar block
    result['registrar']['name'] = result['whois'].get('registrar_name')
    result['registrar']['iana_id'] = result['whois'].get('registrar_iana_id')
    result['registrar']['url'] = result['whois'].get('registrar_url')
    result['registrar']['abuse_email'] = result['whois'].get('registrar_abuse_email')
    result['registrar']['abuse_phone'] = result['whois'].get('registrar_abuse_phone')

    # Infer registrar name from URL if missing
    if (not result['registrar']['name']) and result['registrar']['url']:
        host = result['registrar']['url']
        host = host.replace('http://', '').replace('https://', '').split('/')[0]
        base = host.lower()
        registrar_guess_map = {
            'tucows.com': 'Tucows',
            'godaddy.com': 'GoDaddy',
            'namecheap.com': 'NameCheap',
            'lexsynergy.com': 'Lexsynergy',
            'enom.com': 'eNom',
            'gandi.net': 'Gandi',
            'cloudflare.com': 'Cloudflare',
            'internetbs.net': 'Internet.BS'
        }
        for k, v in registrar_guess_map.items():
            if k in base:
                result['registrar']['name'] = v
                break

    # Normalize date fields
    for k in list(result['whois'].keys()):
        if k in DATE_KEYS:
            result['whois'][k] = parse_date_to_iso(result['whois'][k])

    # Attach contacts
    result['contacts'] = {k: v for k, v in contacts.items() if v}

    return result

# === Domain Enrichment ===
def enrich_domain(domain):
    """Combine all data sources into a single profile."""
    temp_result = {"domain": domain}

    # Create a JSON section for SecurityTrails
    temp_result["securitytrails"] = {}
    # SecurityTrails
    temp_result["securitytrails"].update(securitytrails_domain(domain))
    temp_result["securitytrails"].update(securitytrails_subdomains(domain))


    #Create View DNS section
    temp_result["viewdns"] = {}
    # ViewDNS
    temp_result["viewdns"].update(viewdns_propCheck(domain))
    temp_result["viewdns"].update(viewdns_whois(domain))

    # Create a JSON section for VirusTotal
    temp_result["virustotal"] = {}
    # VirusTotal
    temp_result["virustotal"].update(virustotal_report(domain))
    temp_result["virustotal"].update(virustotal_related_ips(domain))

    # Create a JSON section for DNSDumpster
    temp_result["dnsdumpster"] = {}
    # DNSDumpster
    temp_result["dnsdumpster"].update(dnsdumpster(domain))

    # Generate summary
    summary = generate_summary(domain, temp_result)
    
    # Build final result with summary at top
    result = {
        "summary": summary,
        **temp_result
    }

    # Save to file
    output_filename = f"{domain.replace('.', '_')}_profile.json"
    output_path = os.path.join(output_dir, output_filename)
    with open(output_path, "w", encoding="utf-8") as outfile:
        json.dump(result, outfile, indent=2, ensure_ascii=False)


    return result


def fetchActiveDomains():  # Will take a look at the active domains in our Activity Log and then return them as a list
    """Return list of domains whose is_active flag is True in Domain_Activity_Log.csv.

    Expected CSV header:
        domain,last_checked,is_active,content_hash,content_changed
    """
    activity_log = os.path.join(ROOT_DIR, "Output", "Domain_Activity_Log.csv")
    active_domains = set()
    if not os.path.exists(activity_log):
        print(f"[!] Activity log file not found: {activity_log}")
        return []

    with open(activity_log, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing_cols = {c for c in ("domain", "is_active") if c not in reader.fieldnames}
        if missing_cols:
            print(f"[!] Activity log missing expected columns: {', '.join(missing_cols)}")
            return []
        for row in reader:
            domain = (row.get("domain") or "").strip().lower()
            is_active_raw = (row.get("is_active") or "").strip().lower()
            if not domain:
                continue
            # Treat truthy variants
            if is_active_raw in {"true", "1", "yes", "y"}:
                active_domains.add(domain)

    print(f"[+] Loaded {len(active_domains)} active domains from activity log.")
    return sorted(active_domains)


# === Main Flow ===
def main(input_domain):

    # if flag == True:
    #     #Gonna start iterating thru the active domains in our activity log
    #     active_domains = fetchActiveDomains()
    #     for domain in active_domains:
    #         #first check that the log doesnt exist in the domain profiles for the domain
    #         log_file = os.path.join(ROOT_DIR, "Output", "Domain_Profiles", f"{domain.replace('.', '_')}_profile.json")
    #         if os.path.exists(log_file):
    #             print(f"[!] Domain profile already exists: {log_file}")
    #             continue
    #         else:
    #             print(f"[+] Generating profile for domain: {domain}")
    #             report = enrich_domain(domain)
    #             print("\n[✓] Enriched Domain Report:")
    #             print(json.dumps(report, indent=2, ensure_ascii=False))
    # else:
        
        domain = input_domain
        print(f"[+] Generating profile for domain: {domain}")
        report = enrich_domain(domain)
        print("\n[✓] Enriched Domain Report:")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Usage: python domain_profiler.py <domain>")
        print("Example: python domain_profiler.py example.com")

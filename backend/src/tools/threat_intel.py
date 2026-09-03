"""Threat Intel tools: VirusTotal + AbuseIPDB."""
from __future__ import annotations

import httpx
from langchain_core.tools import tool

from src.config import config


@tool
def query_virustotal(resource: str) -> str:
    """Query VirusTotal for IP, domain, or file hash reputation.
    Returns detection ratio, malicious verdicts, and related metadata.
    Example: query_virustotal("192.168.10.45")"""
    api_key = config.VIRUSTOTAL_API_KEY
    if not api_key:
        return _vt_simulated(resource)

    try:
        with httpx.Client(timeout=10.0) as client:
            if "." in resource and not resource.replace(".", "").isdigit():
                url = f"https://www.virustotal.com/api/v3/domains/{resource}"
            elif resource.replace(".", "").isdigit():
                url = f"https://www.virustotal.com/api/v3/ip_addresses/{resource}"
            else:
                url = f"https://www.virustotal.com/api/v3/files/{resource}"

            resp = client.get(url, headers={"x-apikey": api_key})
            if resp.status_code != 200:
                return f"VirusTotal API error: {resp.status_code}"

            data = resp.json().get("data", {}).get("attributes", {})
            stats = data.get("last_analysis_stats", {})
            return (
                f"VirusTotal: {resource}\n"
                f"  Malicious: {stats.get('malicious', 0)}/{sum(stats.values())}\n"
                f"  Reputation: {data.get('reputation', 'N/A')}\n"
                f"  Categories: {data.get('categories', [])}"
            )
    except Exception as e:
        return f"VirusTotal query failed: {e}"


def _vt_simulated(resource: str) -> str:
    suspicious_ips = {"192.168.10.45", "192.168.10.88", "192.168.10.92"}
    if resource in suspicious_ips:
        return (
            f"VirusTotal [SIMULATED]: {resource}\n"
            f"  Malicious: 12/88 detections\n"
            f"  Reputation: -15 (suspicious)\n"
            f"  Categories: ['malware_c2', 'scanner', 'exploit_kit']\n"
            f"  Last seen: 2026-09-01\n"
            f"  Tags: SQLi_scanner, botnet"
        )
    return f"VirusTotal [SIMULATED]: {resource}\n  Malicious: 0/88\n  Reputation: 0 (clean)"


@tool
def query_abuseipdb(ip: str) -> str:
    """Query AbuseIPDB for IP abuse confidence score.
    Returns confidence score (0-100) and abuse reports count.
    Example: query_abuseipdb("192.168.10.45")"""
    api_key = config.ABUSEIPDB_API_KEY
    if not api_key:
        return _abuse_simulated(ip)

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                "https://api.abuseipdb.com/api/v2/check",
                params={"ipAddress": ip, "maxAgeInDays": 90},
                headers={"Key": api_key, "Accept": "application/json"},
            )
            if resp.status_code != 200:
                return f"AbuseIPDB API error: {resp.status_code}"

            data = resp.json().get("data", {})
            return (
                f"AbuseIPDB: {ip}\n"
                f"  Confidence: {data.get('abuseConfidenceScore', 0)}/100\n"
                f"  Reports: {data.get('totalReports', 0)}\n"
                f"  Country: {data.get('countryCode', 'N/A')}\n"
                f"  Usage: {data.get('usageType', 'N/A')}"
            )
    except Exception as e:
        return f"AbuseIPDB query failed: {e}"


def _abuse_simulated(ip: str) -> str:
    suspicious_ips = {"192.168.10.45", "192.168.10.88", "192.168.10.92"}
    if ip in suspicious_ips:
        return (
            f"AbuseIPDB [SIMULATED]: {ip}\n"
            f"  Confidence: 89/100\n"
            f"  Reports: 47\n"
            f"  Country: CN\n"
            f"  Usage: Data Center/Web Hosting/Transit"
        )
    return f"AbuseIPDB [SIMULATED]: {ip}\n  Confidence: 0/100\n  Reports: 0\n  Country: N/A"

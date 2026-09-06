/**
 * TikTok Request Signer
 * Generates X-Argus, X-Ladon, X-Gorgon headers
 * Based on: https://tiktok-api.seeksocial.io/
 */

import { TikTokConfig } from './tiktok-scraper.js';

export class Signer {
  private config: TikTokConfig;
  private licenseId: string = '7435324743824756473'; // Constant per app

  constructor(config: TikTokConfig) {
    this.config = config;
  }

  /**
   * Generate all required headers for a request
   */
  async generateHeaders(url: string, config: TikTokConfig = this.config): Promise<Record<string, string>> {
    const timestamp = Math.floor(Date.now() / 1000);

    return {
      'x-khronos': timestamp.toString(),
      'x-ladon': await this.generateXLadon(config, timestamp),
      'x-argus': await this.generateXArgus(config, url, timestamp),
      'x-gorgon': await this.generateXGorgon(config, url, timestamp),
      'x-ss-req-ticket': timestamp.toString(),
      'x-tt-trace-id': `00-${this._randomHex(32)}-${this._randomHex(32)}-01`,
    };
  }

  /**
   * Generate X-Ladon header (Speck-128/256 encrypted)
   */
  private async generateXLadon(config: TikTokConfig, timestamp: number): Promise<string> {
    // Simplified - in reality needs Speck-128/256 encryption
    const data = `${config.device_id}${config.iid}${timestamp}${this.licenseId}`;
    const encrypted = await this._speckEncrypt(data);
    return `XKp9${encrypted.substring(0, 32)}`;
  }

  /**
   * Generate X-Argus header (complex digest)
   */
  private async generateXArgus(config: TikTokConfig, url: string, timestamp: number): Promise<string> {
    // Parse URL to extract query params
    const urlObj = new URL(url, 'https://api.tiktok.com');
    const params = urlObj.searchParams;

    // Build query string in exact order (critical!)
    const queryParts: string[] = [];

    // Fixed order from spec
    const paramOrder = [
      'aid', 'iid', 'device_id', 'cdid', 'openudid',
      'device_brand', 'device_type', 'os_version', 'os_api',
      'resolution', 'dpi', 'host_abi', 'region', 'carrier_region',
      'sys_region', 'mcc_mnc', 'language', 'app_language', 'locale',
      'timezone_name', 'version_name', 'version_code', 'manifest_version_code',
      '_rticket', 'channel', 'app_type', 'ts', 'ac', 'ac2', 'x-ss-req-ticket'
    ];

    for (const param of paramOrder) {
      if (params.has(param)) {
        queryParts.push(`${param}=${params.get(param)}`);
      }
    }

    const queryString = queryParts.join('&');

    // Generate digest
    const digest = await this._argusDigest(
      queryString,
      config.device_id,
      config.iid,
      timestamp,
      this.licenseId
    );

    return `cQqbRZm8k1x${digest.substring(0, 64)}`;
  }

  /**
   * Generate X-Gorgon header (legacy digest)
   */
  private async generateXGorgon(
    config: TikTokConfig,
    url: string,
    timestamp: number
  ): Promise<string> {
    // Simplified Gorgon generation
    const data = `${config.device_id}${config.iid}${timestamp}${url}`;
    const hash = await this._sha256(data);
    return `0404b0d30000${hash.substring(0, 32)}`;
  }

  /**
   * Generate Speck-128/256 encrypted string
   */
  private async _speckEncrypt(data: string): Promise<string> {
    // Placeholder - would use actual Speck-128/256 implementation
    const encoded = Buffer.from(data).toString('base64');
    return encoded.substring(0, 64);
  }

  /**
   * Generate X-Argus digest
   */
  private async _argusDigest(
    queryString: string,
    deviceId: string,
    installId: string,
    timestamp: number,
    licenseId: string
  ): Promise<string> {
    // Complex algorithm involving Simon cipher, SM3 hash
    // Simplified for now
    const data = `${queryString}${deviceId}${installId}${timestamp}${licenseId}`;
    return await this._sha256(data);
  }

  /**
   * SHA-256 hash
   */
  private async _sha256(data: string): Promise<string> {
    const encoder = new TextEncoder();
    const encoded = encoder.encode(data);
    const hash = await crypto.subtle.digest('SHA-256', encoded);
    return Array.from(new Uint8Array(hash))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
  }

  /**
   * Generate random hex string
   */
  private _randomHex(length: number): string {
    const chars = '0123456789abcdef';
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars[Math.floor(Math.random() * chars.length)];
    }
    return result;
  }
}

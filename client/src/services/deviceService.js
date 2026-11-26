/**
 * deviceService.js — operaciones sobre netpulse.device
 * La autenticación corre por cookie; uid/apiKey ya no se pasan.
 */
import { callKw } from '../api/odooClient.js';

const FIELDS = ['id', 'name', 'device_type', 'criticality', 'status',
                'gns3_node_id', 'last_seen', 'open_incident_count'];

export function listDevices() {
  return callKw('netpulse.device', 'search_read', [[]], { fields: FIELDS, order: 'name asc' });
}

export async function getDevice(id) {
  const rows = await callKw('netpulse.device', 'search_read',
    [[['id', '=', id]]], { fields: FIELDS });
  return rows?.[0] ?? null;
}

export function createDevice(data) {
  return callKw('netpulse.device', 'create', [data]);
}

export function updateDevice(id, data) {
  return callKw('netpulse.device', 'write', [[id], data]);
}

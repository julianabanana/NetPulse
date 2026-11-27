/**
 * incidentService.js — operaciones sobre netpulse.incident
 */
import { callKw } from '../api/odooClient.js';

const FIELDS = ['id', 'name', 'device_id', 'priority', 'state',
                'technician_id', 'root_cause', 'origin',
                'date_detected', 'date_resolved'];

export function listIncidents(stateFilter = null) {
  const domain = stateFilter ? [['state', '=', stateFilter]] : [];
  return callKw('netpulse.incident', 'search_read', [domain],
    { fields: FIELDS, order: 'date_detected desc' });
}

export function listIncidentsByDevice(deviceId) {
  return callKw('netpulse.incident', 'search_read',
    [[['device_id', '=', deviceId]]],
    { fields: FIELDS, order: 'date_detected desc' });
}

export async function getIncident(id) {
  const rows = await callKw('netpulse.incident', 'search_read',
    [[['id', '=', id]]], { fields: FIELDS });
  return rows?.[0] ?? null;
}

export function createIncident(data) {
  return callKw('netpulse.incident', 'create', [data]);
}

export function updateIncident(id, data) {
  return callKw('netpulse.incident', 'write', [[id], data]);
}

export function startIncident(id) {
  return callKw('netpulse.incident', 'action_start', [[id]]);
}

export function resolveIncident(id) {
  return callKw('netpulse.incident', 'action_resolve', [[id]]);
}

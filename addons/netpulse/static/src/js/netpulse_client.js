/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";

import { api } from "./api_client";
import { createInitialIncidentState, resolveIncidentListState } from "./presentation_state";

export class NetpulseIncidentClient extends Component {
    static template = "netpulse.NetpulseIncidentClient";

    setup() {
        this.state = useState(createInitialIncidentState());

        this.selectIncident = this.selectIncident.bind(this);
        this.changeState = this.changeState.bind(this);
        this.openCreateForm = this.openCreateForm.bind(this);
        this.assignTechnician = this.assignTechnician.bind(this);
        this.updatePriority = this.updatePriority.bind(this);

        onWillStart(() => this.loadIncidentsIfAuthenticated());
    }

    get incidentListState() {
        return resolveIncidentListState(this.state);
    }

    async loadIncidentsIfAuthenticated() {
        if (!api.accessToken || !api.currentUser) {
            return;
        }
        this.state.user = api.currentUser;
        await this.loadIncidents();
    }

    async login() {
        this.state.loading = true;
        this.state.error = "";
        try {
            this.state.user = await api.login(
                this.state.login,
                this.state.password
            );
            this.state.password = "";
            await this.loadIncidents();
        } catch (error) {
            this.state.error = error.message;
        } finally {
            this.state.loading = false;
        }
    }

    async loadIncidents() {
        this.state.loading = true;
        this.state.error = "";
        try {
            const result = await api.listIncidents();
            this.state.incidents = result.items || [];
            this.state.selectedIncident = null;
        } catch (error) {
            this.state.error = error.message;
            if (error.status === 401) {
                this.state.user = null;
            }
        } finally {
            this.state.loading = false;
        }
    }

    async openCreateForm() {
        this.state.showCreateForm = !this.state.showCreateForm;
        if (!this.state.showCreateForm) {
            return;
        }
        this.state.error = "";
        try {
            const devicesResult = await api.listDevices();
            this.state.devices = devicesResult.items || [];
            if (this.state.user.role === "admin") {
                const techniciansResult = await api.listTechnicians();
                this.state.technicians = techniciansResult.items || [];
            }
        } catch (error) {
            this.state.error = error.message;
        }
    }

    async assignTechnician() {
        if (!this.state.selectedIncident || !this.state.selectedTechnicianId) {
            return;
        }
        this.state.submitting = true;
        this.state.error = "";
        this.state.notice = "";
        try {
            const incidentId = this.state.selectedIncident.id;
            await api.assignTechnician(incidentId, this.state.selectedTechnicianId);
            await this.selectIncident({ id: incidentId });
            await this.loadIncidents();
            await this.selectIncident({ id: incidentId });
            this.state.notice = "El técnico se asignó correctamente.";
        } catch (error) {
            this.state.error = error.message;
        } finally {
            this.state.submitting = false;
        }
    }

    async selectIncident(incident) {
        this.state.error = "";
        this.state.notice = "";
        this.state.loading = true;
        try {
            this.state.selectedIncident = await api.getIncident(incident.id);
            this.state.selectedTechnicianId = this.state.selectedIncident.technician_id
                ? String(this.state.selectedIncident.technician_id[0])
                : "";
            this.state.selectedPriority = String(this.state.selectedIncident.priority);
            if (this.state.user.role === "admin" && !this.state.technicians.length) {
                const result = await api.listTechnicians();
                this.state.technicians = result.items || [];
            }
        } catch (error) {
            this.state.error = error.message;
            if (error.status === 401) {
                this.state.user = null;
            }
        } finally {
            this.state.loading = false;
        }
    }

    async updatePriority() {
        if (
            !this.state.selectedIncident ||
            this.state.user.role !== "admin" ||
            !["0", "1", "2"].includes(this.state.selectedPriority)
        ) {
            return;
        }
        this.state.submitting = true;
        this.state.error = "";
        this.state.notice = "";
        try {
            const incidentId = this.state.selectedIncident.id;
            await api.updatePriority(incidentId, this.state.selectedPriority);
            await this.selectIncident({ id: incidentId });
            this.state.notice = "La prioridad se actualizó correctamente.";
        } catch (error) {
            this.state.error = error.message;
        } finally {
            this.state.submitting = false;
        }
    }

    async createIncident() {
        this.state.submitting = true;
        this.state.error = "";
        this.state.notice = "";
        try {
            await api.createIncident({
                device_id: Number(this.state.deviceId),
                description: this.state.description,
                root_cause: this.state.rootCause,
                ...(this.state.user.role === "admin"
                    ? {
                        priority: this.state.priority,
                        ...(this.state.technicianId
                            ? { technician_id: Number(this.state.technicianId) }
                            : {}),
                    }
                    : {}),
            });
            this.state.deviceId = "";
            this.state.description = "";
            this.state.rootCause = "";
            this.state.priority = "1";
            this.state.technicianId = "";
            this.state.showCreateForm = false;
            this.state.notice = "La incidencia se creó correctamente.";
            await this.loadIncidents();
        } catch (error) {
            this.state.error = error.message;
            if (error.status === 401) {
                this.state.user = null;
            }
        } finally {
            this.state.submitting = false;
        }
    }

    async changeState(nextState) {
        if (!this.state.selectedIncident) {
            return;
        }
        this.state.submitting = true;
        this.state.error = "";
        this.state.notice = "";
        try {
            await api.updateState(this.state.selectedIncident.id, nextState);
            this.state.notice = "El estado de la incidencia se actualizó.";
            const incidentId = this.state.selectedIncident.id;
            await this.loadIncidents();
            await this.selectIncident({ id: incidentId });
            this.state.notice = "El estado de la incidencia se actualizó.";
        } catch (error) {
            this.state.error = error.message;
            if (error.status === 401) {
                this.state.user = null;
            }
        } finally {
            this.state.submitting = false;
        }
    }

    logout() {
        api.logout();
        this.state.user = null;
        this.state.incidents = [];
        this.state.selectedIncident = null;
        this.state.notice = "";
        this.state.error = "";
    }
}

registry.category("actions").add(
    "netpulse_incident_client",
    NetpulseIncidentClient
);

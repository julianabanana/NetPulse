/** @odoo-module **/

/** Cliente HTTP independiente de la interfaz OWL. */

export class NetpulseApiClient {
    constructor(
        baseUrl = "/api/v1",
        fetchImplementation = globalThis.fetch.bind(globalThis)
    ) {
        this.baseUrl = baseUrl;
        this.fetchImplementation = fetchImplementation;
        this.accessToken = null;
        this.currentUser = null;
    }

    async request(path, options = {}) {
        const headers = new Headers(options.headers || {});
        headers.set("Accept", "application/json");

        if (options.body) {
            headers.set("Content-Type", "application/json");
        }
        if (this.accessToken) {
            headers.set("Authorization", `Bearer ${this.accessToken}`);
        }

        const response = await this.fetchImplementation(
            `${this.baseUrl}${path}`,
            {
                ...options,
                headers,
            }
        );
        const payload = await response.json().catch(() => ({}));

        if (response.status === 401) {
            this.accessToken = null;
            this.currentUser = null;
            const error = new Error(
                "Tu sesión expiró. Inicia sesión nuevamente."
            );
            error.status = 401;
            throw error;
        }
        if (response.status === 403) {
            const error = new Error(
                "No tienes permisos para realizar esta acción."
            );
            error.status = 403;
            throw error;
        }
        if (!response.ok) {
            const error = new Error(
                payload.message || "No fue posible completar la solicitud."
            );
            error.status = response.status;
            throw error;
        }
        return payload;
    }

    async login(login, password) {
        const payload = await this.request("/auth/login", {
            method: "POST",
            body: JSON.stringify({ login, password }),
        });
        this.accessToken = payload.access_token;
        this.currentUser = payload.user;
        return this.currentUser;
    }

    listIncidents() {
        return this.request("/incidents");
    }

    listDevices() {
        return this.request("/devices");
    }

    getIncident(id) {
        return this.request(`/incidents/${id}`);
    }

    createIncident(values) {
        return this.request("/incidents", {
            method: "POST",
            body: JSON.stringify(values),
        });
    }

    listTechnicians() {
        return this.request("/technicians");
    }

    assignTechnician(id, technicianId) {
        return this.request(`/incidents/${id}/assignment`, {
            method: "PATCH",
            body: JSON.stringify({ technician_id: Number(technicianId) }),
        });
    }

    updatePriority(id, priority) {
        return this.request(`/incidents/${id}/priority`, {
            method: "PATCH",
            body: JSON.stringify({ priority: String(priority) }),
        });
    }

    updateState(id, state) {
        return this.request(`/incidents/${id}/state`, {
            method: "PATCH",
            body: JSON.stringify({ state }),
        });
    }

    logout() {
        this.accessToken = null;
        this.currentUser = null;
    }
}

export const api = new NetpulseApiClient();

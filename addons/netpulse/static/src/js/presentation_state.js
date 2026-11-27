/** @odoo-module **/

/** Funciones puras para representar los estados de la lista de incidencias. */

export function createInitialIncidentState() {
    return {
        login: "",
        password: "",
        user: null,
        incidents: [],
        selectedIncident: null,
        deviceId: "",
        devices: [],
        description: "",
        rootCause: "",
        priority: "1",
        technicianId: "",
        technicians: [],
        selectedTechnicianId: "",
        selectedPriority: "1",
        loading: false,
        submitting: false,
        error: "",
        notice: "",
        showCreateForm: false,
    };
}

export function resolveIncidentListState(state) {
    if (state.loading) {
        return "loading";
    }
    if (state.error) {
        return "error";
    }
    if (!state.incidents || state.incidents.length === 0) {
        return "empty";
    }
    return "success";
}

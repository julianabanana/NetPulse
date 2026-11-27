import assert from "node:assert/strict";
import { test } from "node:test";

import {
    createInitialIncidentState,
    resolveIncidentListState,
} from "../../static/src/js/presentation_state.js";

test("la lista vacía produce el estado vacío", () => {
    const state = createInitialIncidentState();

    assert.equal(resolveIncidentListState(state), "empty");
    assert.deepEqual(state.devices, []);
});

test("un error de red produce el estado de error", () => {
    const state = createInitialIncidentState();
    state.error = "No fue posible conectar con el servidor.";

    assert.equal(resolveIncidentListState(state), "error");
});

import { test } from "node:test";
import assert from "node:assert/strict";
import { candidates } from "./logo-picker-probe.mjs";

test("Use Easee ownership, preserve source names, exclude selected and disabled devices", () => {
  const entries = [{ entry_id: "easee-source", domain: "easee" },
    { entry_id: "slm", domain: "smart_load_manager" }];
  const devices = [
    { id: "a", name: "Garage", config_entries: ["easee-source"] },
    { id: "b", name: "Carport", name_by_user: "My carport", config_entries: ["easee-source"] },
    { id: "mirror", name: "Garage", config_entries: ["slm"] },
    { id: "disabled", disabled_by: "user", config_entries: ["easee-source"] },
    { id: "other", config_entries: ["other-source"] },
  ];
  assert.deepEqual(candidates(devices, entries), [
    { id: "a", name: "Garage" }, { id: "b", name: "My carport" },
  ]);
  assert.deepEqual(candidates(devices, entries, ["a"]), [{ id: "b", name: "My carport" }]);
  assert.equal(devices[0].name, "Garage");
});

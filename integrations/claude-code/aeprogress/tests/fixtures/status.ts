// What `aepkit status --json` prints for the sample run in the repository's
// tests/test_status.py (SAMPLE_PLAN, SAMPLE_GUIDE, SAMPLE_LOG), which checks it still does.
export const STATUS = {
  "schema": 1,
  "items": [
    {
      "id": "P0-T1",
      "phase": 0,
      "kind": "task",
      "state": "APPROVED",
      "verdict": "APPROVED",
      "report": null,
      "executor": "Ana",
      "conflict": null,
      "inLog": true
    },
    {
      "id": "P0-G1",
      "phase": 0,
      "kind": "gate",
      "state": "APPROVED",
      "verdict": "APPROVED",
      "report": null,
      "executor": "Ana",
      "conflict": null,
      "inLog": true
    },
    {
      "id": "P1-T1",
      "phase": 1,
      "kind": "task",
      "state": "APPROVED",
      "verdict": "APPROVED",
      "report": null,
      "executor": "Bo",
      "conflict": null,
      "inLog": true
    },
    {
      "id": "P1-T2",
      "phase": 1,
      "kind": "task",
      "state": "CONDITIONAL",
      "verdict": "CONDITIONAL",
      "report": null,
      "executor": "Bo",
      "conflict": null,
      "inLog": true
    },
    {
      "id": "P1-T3",
      "phase": 1,
      "kind": "task",
      "state": "AWAITING AUDIT",
      "verdict": null,
      "report": "DONE",
      "executor": "Cy",
      "conflict": null,
      "inLog": true
    },
    {
      "id": "P1-G1",
      "phase": 1,
      "kind": "gate",
      "state": "PENDING",
      "verdict": null,
      "report": null,
      "executor": null,
      "conflict": null,
      "inLog": true
    }
  ],
  "phases": [
    {
      "number": 0,
      "id": "P0",
      "title": "Groundwork",
      "weight": 1.0,
      "brokenDown": true,
      "items": [
        "P0-T1",
        "P0-G1"
      ]
    },
    {
      "number": 1,
      "id": "P1",
      "title": "The core feature",
      "weight": 2.0,
      "brokenDown": true,
      "items": [
        "P1-T1",
        "P1-T2",
        "P1-T3",
        "P1-G1"
      ]
    },
    {
      "number": 2,
      "id": "P2",
      "title": "Hardening",
      "weight": 1.0,
      "brokenDown": false,
      "items": []
    }
  ],
  "counts": {
    "APPROVED": 3,
    "AWAITING AUDIT": 1,
    "CONDITIONAL": 1,
    "PENDING": 1
  },
  "open": [
    "P1-T2",
    "P1-T3",
    "P1-G1"
  ],
  "mostRecent": {
    "id": "P1-T3",
    "state": "AWAITING AUDIT"
  },
  "documents": {
    "executionGuide": true,
    "planOfRecord": true
  }
}

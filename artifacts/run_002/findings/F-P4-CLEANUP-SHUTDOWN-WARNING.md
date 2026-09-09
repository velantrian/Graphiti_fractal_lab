# F-P4-CLEANUP-SHUTDOWN-WARNING

severity: MINOR
category: RESOURCE_CLEANUP

```json
{
  "warning_name": "coroutine 'AsyncManagementCommands.shutdown' was never awaited",
  "severity_during_aclose_in_this_test": false,
  "severity": "MINOR",
  "category": "RESOURCE_CLEANUP",
  "note": "Known redislite/FalkorDBLite teardown noise. Lab bootstrap prefers AsyncFalkorDB.close() over FalkorDriver.close()/aclose-only. No obvious one-line fix without invasive redislite changes; left as finding.",
  "pytest_filter": "tests filterwarnings ignore this RuntimeWarning"
}
```

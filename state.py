# In-memory registry mapping survey_id -> built Excel file path.
# Process-local only; a restart clears it, matching this app's current
# no-database scope.
SURVEYS: dict[str, str] = {}

# Registry mapping survey_id -> the submitted survey payload (model_dump()),
# kept so a survey can be rebuilt after late photo uploads. Also
# process-local only.
SURVEY_DATA: dict[str, dict] = {}

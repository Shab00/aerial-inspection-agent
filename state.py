# In-memory registry mapping survey_id -> built Excel file path.
# Process-local only; a restart clears it, matching this app's current
# no-database scope.
SURVEYS: dict[str, str] = {}

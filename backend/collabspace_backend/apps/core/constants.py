# Application-wide constants:

# Defines the roles a user can have within a Workspace.
# Typically used for permission checks and UI display.
WORKSPACE_ROLES = {
    'OWNER': 'Owner',            # Highest level of access, usually only one per workspace
    'ADMIN': 'Administrator',    # High access, manages users and settings
    'MEMBER': 'Member',          # Standard user, can create and manage tasks/projects
    'GUEST': 'Guest',            # Limited access, usually only to assigned items
}

# Defines the possible lifecycle stages for a Project.
PROJECT_STATUSES = {
    'PLANNING': 'Planning',        # Project is being defined and scoped
    'ACTIVE': 'Active',            # Project is currently being worked on
    'ON_HOLD': 'On Hold',          # Work is temporarily paused
    'COMPLETED': 'Completed',      # Project goals have been met
    'ARCHIVED': 'Archived',        # Project is no longer relevant but kept for history
}

# Defines the possible lifecycle stages for an individual Task.
TASK_STATUSES = {
    'TODO': 'To Do',            # Task has been created and is waiting to start
    'IN_PROGRESS': 'In Progress',  # Task is currently being worked on
    'REVIEW': 'In Review',       # Task is complete and awaiting validation
    'BLOCKED': 'Blocked',        # Task cannot proceed due to a dependency or issue
    'DONE': 'Done',              # Task is complete and accepted
}

# Defines the relative importance of a Task.
TASK_PRIORITIES = {
    'LOW': 1,
    'MEDIUM': 2,
    'HIGH': 3,
    'CRITICAL': 4,
}

# --- File Upload Configuration ---
# Maximum size for file uploads, 10MB (10 * 1024 * 1024 bytes)
# This constraint is often tied to service limits (e.g., Cloudinary free tier).
FILE_MAX_SIZE = 10485760

# Maximum size for *audio* uploads (e.g., for transcription), set slightly higher at 20MB.
AUDIO_MAX_SIZE = 20971520 

# Allowed MIME types for file uploads to maintain security and compatibility.
ALLOWED_FILE_TYPES = [
    'image/jpeg',
    'image/png',
    'image/gif',
    'application/pdf',
    'text/plain',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', # .xlsx
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', # .docx
    
    # --- ADDED AUDIO TYPES ---
    'audio/mpeg',        # .mp3
    'audio/wav',         # .wav
    'audio/ogg',         # .ogg
    'audio/webm',        # Common for web recording
]

# --- AI Service Usage Limits ---
# AI Service Usage Limits based on the subscription plan.
# Values are used to enforce daily quotas and control API call complexity.
AI_USAGE_LIMITS = {
    'free': {
        'daily_requests': 60,       # Daily limit on the number of API calls
        'tokens_per_request': 1000  # Max output tokens allowed per request
    },
    'pro': {
        'daily_requests': 1500,
        'tokens_per_request': 4000
    },
    'enterprise': {
        'daily_requests': -1,       # -1 typically means unlimited or a very high custom limit
        'tokens_per_request': 8000
    }
}

# Mapping of internal model aliases to the actual Google Gemini API model names.
GEMINI_MODELS = {
    'flash': 'gemini-1.5-flash',  # Fast, efficient, general-purpose model
    'pro': 'gemini-1.5-pro'       # More capable, better for complex reasoning (supports multimodal, including audio)
}

# --- Default settings ---
DEFAULT_WORKSPACE_NAME = "My New Workspace"
DEFAULT_TASK_PRIORITY = TASK_PRIORITIES['MEDIUM']
DEFAULT_TASK_STATUS = TASK_STATUSES['TODO']
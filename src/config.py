COMMAND_PREFIX = "="

# XP earned per eligible message
XP_MIN = 5
XP_MAX = 15

# Seconds a user must wait between messages that earn XP (prevents spam farming)
XP_COOLDOWN_SECONDS = 60

# Total XP needed to reach a given layer: xp_for_layer(n) = XP_PER_LAYER * n
XP_PER_LAYER = 100
MAX_LAYER = 13

# =daily command
DAILY_XP_MIN = 50
DAILY_XP_MAX = 100
DAILY_COOLDOWN_SECONDS = 24 * 60 * 60

# XP for reacting to messages
REACTION_XP_MIN = 2
REACTION_XP_MAX = 5
REACTION_XP_COOLDOWN_SECONDS = 60

# XP for being active in a voice channel (with at least one other non-bot member)
VOICE_XP_MIN = 3
VOICE_XP_MAX = 8
VOICE_XP_INTERVAL_SECONDS = 60

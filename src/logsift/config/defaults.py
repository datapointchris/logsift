"""Default configuration values.

Defines sensible defaults for all configuration options.
"""

from pathlib import Path

DEFAULT_CONFIG = {
    'general': {
        'cache_dir': Path.home() / '.cache' / 'logsift',
        'default_interval': 60,
    },
    'output': {
        'default_format': 'auto',
        'use_colors': True,
        'use_emoji': True,
        'context_lines': 2,
    },
    'summary': {
        'max_errors': 10,
        'max_warnings': 5,
        'show_line_numbers': True,
        'show_context': True,
        'show_suggestions': True,
        'deduplicate_errors': True,
    },
    'patterns': {
        'load_builtin': True,
        'load_custom': True,
        'custom_dir': Path.home() / '.config' / 'logsift' / 'patterns',
    },
    'notifications': {
        'enabled': True,
        'on_success': False,
        'on_failure': True,
    },
    'cleanup': {
        'retention_days': 90,
        'auto_cleanup': False,
    },
    'monitor': {
        'check_interval': 60,
        'show_progress': True,
        'save_logs': True,
    },
    'watch': {
        'update_interval': 1,
        'clear_screen': False,
    },
}

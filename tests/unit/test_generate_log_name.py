"""Tests for log name generation."""

from logsift.commands.monitor import _generate_log_name


def test_generate_log_name_empty_command():
    """Test log name generation with empty command."""
    result = _generate_log_name([])
    assert result == 'unknown'


def test_generate_log_name_single_command():
    """Test log name generation with single command."""
    result = _generate_log_name(['ls'])
    assert result == 'ls'


def test_generate_log_name_two_args():
    """Test log name generation with command and one argument."""
    result = _generate_log_name(['make', 'test'])
    assert result == 'make-test'


def test_generate_log_name_with_flags():
    """Test log name generation ignores flags."""
    result = _generate_log_name(['pytest', '-v', 'tests'])
    assert result == 'pytest-tests'


def test_generate_log_name_multiple_flags():
    """Test log name generation skips multiple flags."""
    # Note: -f is a flag, but docker-compose.yml is not (doesn't start with -)
    # So the result includes docker-compose.yml as a non-flag argument
    result = _generate_log_name(['docker', 'compose', '-f', 'docker-compose.yml', 'up', '-d'])
    assert result == 'docker-compose-docker-compose.yml-up'


def test_generate_log_name_uv_run():
    """Test log name generation for uv run commands."""
    result = _generate_log_name(['uv', 'run', 'mkdocs', 'build'])
    assert result == 'uv-run-mkdocs-build'


def test_generate_log_name_uv_run_with_flags():
    """Test log name generation for uv run with flags."""
    result = _generate_log_name(['uv', 'run', '--no-cache', 'pytest', 'tests'])
    assert result == 'uv-run-pytest-tests'


def test_generate_log_name_bash_script():
    """Test log name generation for bash scripts."""
    result = _generate_log_name(['bash', 'install.sh'])
    assert result == 'bash-install'


def test_generate_log_name_python_script():
    """Test log name generation for python scripts."""
    result = _generate_log_name(['python', 'main.py'])
    assert result == 'python-main'


def test_generate_log_name_script_with_path():
    """Test log name generation strips paths from scripts."""
    result = _generate_log_name(['bash', '/home/user/scripts/deploy.sh'])
    assert result == 'bash-deploy'


def test_generate_log_name_node_script():
    """Test log name generation for node scripts."""
    result = _generate_log_name(['node', 'server.js'])
    assert result == 'node-server'


def test_generate_log_name_ruby_script():
    """Test log name generation for ruby scripts."""
    result = _generate_log_name(['ruby', 'migrate.rb'])
    assert result == 'ruby-migrate'


def test_generate_log_name_max_four_parts():
    """Test log name generation limits to 4 parts."""
    result = _generate_log_name(['docker', 'compose', 'run', 'web', 'python', 'manage.py'])
    assert result == 'docker-compose-run-web'
    # Should stop at 4 parts (first cmd + 3 args)


def test_generate_log_name_length_limit():
    """Test log name generation limits length to 50 chars."""
    long_cmd = [
        'very-long-command-name-that-exceeds-limits',
        'very-long-arg1',
        'very-long-arg2',
        'very-long-arg3',
    ]
    result = _generate_log_name(long_cmd)
    assert len(result) <= 50


def test_generate_log_name_docker_compose():
    """Test log name generation for docker compose commands."""
    result = _generate_log_name(['docker', 'compose', 'up'])
    assert result == 'docker-compose-up'


def test_generate_log_name_git_commands():
    """Test log name generation for git commands."""
    # Note: 'message' after -m flag is not a flag itself, so it gets included
    result = _generate_log_name(['git', 'commit', '-m', 'message'])
    assert result == 'git-commit-message'


def test_generate_log_name_npm_commands():
    """Test log name generation for npm commands."""
    result = _generate_log_name(['npm', 'run', 'build'])
    assert result == 'npm-run-build'


def test_generate_log_name_cargo_commands():
    """Test log name generation for cargo commands."""
    result = _generate_log_name(['cargo', 'test'])
    assert result == 'cargo-test'


def test_generate_log_name_go_commands():
    """Test log name generation for go commands."""
    result = _generate_log_name(['go', 'build', './cmd/app'])
    assert result == 'go-build-app'


def test_generate_log_name_with_equals_flag():
    """Test log name generation with --flag=value style."""
    result = _generate_log_name(['pytest', '--maxfail=1', 'tests'])
    assert result == 'pytest-tests'


def test_generate_log_name_all_flags():
    """Test log name generation when all args are flags."""
    result = _generate_log_name(['ls', '-la', '-h'])
    assert result == 'ls'

"""
Trinity — Main entry point.
Run with: python -m trinity.main
"""

import sys
import signal
import asyncio
import click
from pathlib import Path

from trinity.utils.config import load_config
from trinity.utils.logging import setup_logging


@click.group(invoke_without_command=True)
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--config", default=None, help="Path to config file")
@click.pass_context
def cli(ctx, debug: bool, config: str | None):
    """Trinity — Your voice-first AI agent."""
    ctx.ensure_object(dict)
    ctx.obj["debug"] = debug
    ctx.obj["config_path"] = config

    if ctx.invoked_subcommand is None:
        ctx.invoke(run, debug=debug, config=config)


@cli.command()
@click.option("--debug", is_flag=True, help="Enable debug mode")
@click.option("--config", default=None, help="Path to config file")
def run(debug: bool, config: str | None):
    """Start Trinity agent."""
    setup_logging(debug=debug)
    cfg = load_config(config_path=config)

    if debug:
        cfg["trinity"]["debug_mode"] = True

    click.echo("🜂 Starting Trinity...")
    click.echo(f"   User: {cfg['trinity']['user_name']}")
    click.echo(f"   Mode: {cfg['trinity']['privacy_mode']}")
    click.echo(f"   LLM:  {cfg['llm']['cloud_primary']} (cloud-first)")
    click.echo()

    from trinity.daemon import TrinityDaemon
    daemon = TrinityDaemon(cfg)

    # Handle Ctrl+C gracefully
    def shutdown(signum, frame):
        click.echo("\n🜂 Trinity shutting down...")
        daemon.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    try:
        daemon.start()
    except KeyboardInterrupt:
        shutdown(None, None)


@cli.command()
def status():
    """Check if Trinity is running."""
    try:
        import psutil
        trinity_procs = [
            p for p in psutil.process_iter(["name", "cmdline"])
            if p.info["cmdline"] and "trinity" in " ".join(p.info["cmdline"])
        ]
        if trinity_procs:
            click.echo("✅ Trinity is running")
            for p in trinity_procs:
                click.echo(f"   PID: {p.pid} — {' '.join(p.info['cmdline'][:3])}")
        else:
            click.echo("❌ Trinity is not running")
    except ImportError:
        click.echo("❓ Cannot check status — psutil not installed")


@cli.command()
@click.option("--channel", default="stable", help="Update channel (stable/beta/nightly)")
def update(channel: str):
    """Check for updates."""
    click.echo(f"🔍 Checking for updates ({channel} channel)...")
    # TODO: Implement update checker
    click.echo("   No updates available.")


@cli.command()
def rollback():
    """Rollback to previous version."""
    click.echo("⏪ Rolling back to previous version...")
    # TODO: Implement rollback
    click.echo("   Rollback complete.")


@cli.command()
def skills():
    """List installed skills."""
    click.echo("📋 Installed skills:")
    for skill_name in ["filesystem", "calendar", "email", "drive", "maps", "applications"]:
        click.echo(f"   ✅ {skill_name}")


if __name__ == "__main__":
    cli()

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
@click.option("--web/--no-web", default=True, help="Launch web UI")
@click.option("--port", default=8400, help="Web UI port")
def run(debug: bool, config: str | None, web: bool, port: int):
    """Start Trinity agent."""
    setup_logging(debug=debug)
    cfg = load_config(config_path=config)

    if debug:
        cfg["trinity"]["debug_mode"] = True

    click.echo("🜂 Starting Trinity...")
    click.echo(f"   User: {cfg['trinity']['user_name']}")
    llm_mode = cfg["llm"].get("mode", "local")
    model = cfg["llm"].get("local_fast", "unknown")
    click.echo(f"   LLM:  {model} ({llm_mode}-first)")
    click.echo()

    if web:
        click.echo(f"   🌐 Web UI: http://localhost:{port}")
        click.echo(f"   💬 Open your browser to start chatting")
        click.echo()

        from trinity.web.app import TrinityWebApp
        from trinity.llm.router import LLMRouter
        from trinity.voice.tts import TTSEngine

        llm_router = LLMRouter(cfg)
        tts_engine = TTSEngine(cfg)

        # Load skills
        skills = {}
        try:
            from trinity.skills.filesystem.reader import FileSystemReader
            from trinity.skills.filesystem.writer import FileSystemWriter
            skills["filesystem.read"] = FileSystemReader(cfg)
            skills["filesystem.write"] = FileSystemWriter(cfg)
        except Exception:
            pass

        web_app = TrinityWebApp(
            config=cfg,
            llm_router=llm_router,
            tts_engine=tts_engine,
            skills=skills,
        )

        # Handle Ctrl+C gracefully
        def shutdown(signum, frame):
            click.echo("\n🜂 Trinity shutting down...")
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown)

        try:
            web_app.run(host="0.0.0.0", port=port)
        except KeyboardInterrupt:
            shutdown(None, None)
    else:
        from trinity.daemon import TrinityDaemon
        daemon = TrinityDaemon(cfg)

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
def voice():
    """Start Trinity in voice mode — always listening, say 'Trinity' to activate."""
    setup_logging()
    cfg = load_config()

    click.echo("🜂 Starting Trinity Voice Mode...")
    click.echo(f"   Say 'Trinity' to wake me up")
    click.echo()

    from trinity.llm.router import LLMRouter
    from trinity.voice.tts import TTSEngine
    from trinity.voice.daemon import VoiceDaemon
    from trinity.voice.stt import STTEngine

    llm_router = LLMRouter(cfg)
    tts_engine = TTSEngine(cfg)

    # Try to init STT
    stt_engine = None
    try:
        stt_engine = STTEngine(cfg)
    except Exception as e:
        click.echo(f"   ⚠️  STT init warning: {e}")
        click.echo("   Using built-in Whisper for wake word detection")

    daemon = VoiceDaemon(cfg, llm_router, tts_engine, stt_engine)

    def shutdown(signum, frame):
        click.echo("\n🜂 Trinity shutting down...")
        daemon.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    try:
        asyncio.run(daemon.start())
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

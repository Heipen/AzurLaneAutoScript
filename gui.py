import threading
from multiprocessing import Event, Process

from module.logger import logger
from module.webui.setting import State


def func(ev: threading.Event):
    import argparse
    import asyncio
    import sys

    import uvicorn

    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    State.restart_event = ev

    parser = argparse.ArgumentParser(description="Alas web service")
    parser.add_argument(
        "--host",
        type=str,
        help="Host to listen. Default to WebuiHost in deploy setting",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="Port to listen. Default to WebuiPort in deploy setting",
    )
    parser.add_argument(
        "-k", "--key", type=str, help="Password of alas. No password by default"
    )
    parser.add_argument(
        "--cdn",
        action="store_true",
        help="Use jsdelivr cdn for pywebio static files (css, js). Self host cdn by default.",
    )
    parser.add_argument(
        "--electron", action="store_true", help="Runs by electron client."
    )
    parser.add_argument(
        "--ssl-key", dest="ssl_key", type=str, help="SSL key file path for HTTPS support"
    )
    parser.add_argument(
        "--ssl-cert", type=str, help="SSL certificate file path for HTTPS support"
    )
    parser.add_argument(
        "--run",
        nargs="+",
        type=str,
        help="Run alas by config names on startup",
    )
    args, _ = parser.parse_known_args()

    host = args.host or State.deploy_config.WebuiHost or "0.0.0.0"
    port = args.port or int(State.deploy_config.WebuiPort) or 22267
    ssl_key = args.ssl_key or State.deploy_config.WebuiSSLKey
    ssl_cert = args.ssl_cert or State.deploy_config.WebuiSSLCert
    ssl = ssl_key is not None and ssl_cert is not None
    State.electron = args.electron

    logger.hr("Launcher config")
    logger.attr("Host", host)
    logger.attr("Port", port)
    logger.attr("SSL", ssl)
    logger.attr("Electron", args.electron)
    logger.attr("Reload", ev is not None)

    if State.electron:
        # https://github.com/LmeSzinc/AzurLaneAutoScript/issues/2051
        logger.info("Electron detected, remove log output to stdout")
        from module.logger import console_hdlr
        logger.removeHandler(console_hdlr)

    if ssl_cert is None and ssl_key is not None:
        logger.error("SSL key provided without certificate. Please provide both SSL key and certificate.")
    elif ssl_key is None and ssl_cert is not None:
        logger.error("SSL certificate provided without key. Please provide both SSL key and certificate.")

    if ssl:
        uvicorn.run("module.webui.app:app", host=host, port=port, factory=True, ssl_keyfile=ssl_key, ssl_certfile=ssl_cert)
    else:
        uvicorn.run("module.webui.app:app", host=host, port=port, factory=True)

def run_cl1_migration():
    """
    启动时尝试迁移 CL1 统计数据 (JSON -> SQLite)
    """
    try:
        from pathlib import Path
        from module.statistics.cl1_database import db, Cl1Database
        logger.hr("Checking CL1 Migration")
        
        project_root = Path(__file__).parent
        log_dir = project_root / 'log' / 'cl1'
        
        if not log_dir.exists():
            logger.warning(f"Log directory not found: {log_dir}")
            return

        migrated_count = 0
        dependencies = [p for p in log_dir.iterdir()]
        logger.info(f"Scanning {log_dir}, found {len(dependencies)} items: {[p.name for p in dependencies]}")

        # 扫描 log/cl1 下的所有子文件夹
        for instance_dir in dependencies:
            if instance_dir.is_dir():
                json_file = instance_dir / 'cl1_monthly.json'
                if json_file.exists():
                    logger.info(f"Found legacy data for instance: {instance_dir.name}")
                    try:
                        db.migrate_from_json(json_file, instance_dir.name)
                        migrated_count += 1
                    except Exception as e:
                        logger.error(f"Failed to migrate {instance_dir.name}: {e}")
                else:
                     logger.info(f"No cl1_monthly.json in {instance_dir.name}")
            else:
                logger.info(f"Skipping non-directory: {instance_dir.name}")
        
        if migrated_count > 0:
            logger.info(f"Migration completed for {migrated_count} instance(s).")
            
    except Exception as e:
        logger.exception(f"Error during CL1 migration check: {e}")

if __name__ == "__main__":
    # 尝试迁移 CL1 数据
    run_cl1_migration()
    if State.deploy_config.EnableReload:
        should_exit = False
        while not should_exit:
            event = Event()
            process = Process(target=func, args=(event,))
            process.start()
            while not should_exit:
                try:
                    b = event.wait(1)
                except KeyboardInterrupt:
                    should_exit = True
                    break
                if b:
                    process.kill()
                    break
                elif process.is_alive():
                    continue
                else:
                    should_exit = True
    else:
        func(None)

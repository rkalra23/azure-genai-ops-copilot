import logging
from azure.monitor.opentelemetry import configure_azure_monitor


logger = logging.getLogger(__name__)


def setup_telemetry(connection_string: str) -> None:
    """
    Configure Azure Monitor / Application Insights telemetry if a
    connection string is available.
    """
    if not connection_string:
        logger.info("Azure Monitor connection string not provided. Telemetry disabled.")
        return

    try:
        configure_azure_monitor(connection_string=connection_string)
        logger.info("Azure Monitor telemetry configured successfully.")
    except Exception as exc:
        logger.exception("Failed to configure Azure Monitor telemetry: %s", exc)
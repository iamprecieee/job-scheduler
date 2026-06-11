import asyncio
from typing import Any


class GenerateReportHandler:
    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Mock report generation."""
        # Simulate processing time
        await asyncio.sleep(2.0)

        report_type = payload.get("report_type", "daily_summary")
        return {
            "status": "success",
            "message": f"Report '{report_type}' generated successfully",
            "report_url": "https://example.com/reports/mock-report.pdf",
            "size_bytes": 1048576,
        }


class UploadFileHandler:
    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Mock file upload."""
        # Simulate upload latency
        await asyncio.sleep(1.5)

        file_name = payload.get("file_name", "unknown.pdf")
        destination = payload.get("destination", "s3://mock-bucket")
        return {
            "status": "success",
            "message": f"File '{file_name}' uploaded to {destination}",
            "upload_id": "up_mock12345",
        }

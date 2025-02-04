# backend/api/metrics.py
from fastapi import APIRouter, HTTPException
import psutil
import platform
import GPUtil
import logging

router = APIRouter()

@router.get("/metrics")
def get_hardware_metrics():
    try:
        # CPU metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        per_core_usage = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq().current if psutil.cpu_freq() else None
        
        # Memory metrics
        virtual_mem = psutil.virtual_memory()
        memory_usage_percent = virtual_mem.percent
        memory_used = virtual_mem.used
        memory_total = virtual_mem.total

        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_read = disk_io.read_bytes if disk_io else None
        disk_write = disk_io.write_bytes if disk_io else None

        # GPU metrics
        gpu_metrics = []
        try:
            gpus = GPUtil.getGPUs()
            for gpu in gpus:
                gpu_metrics.append({
                    "name": gpu.name,
                    "load": gpu.load * 100,
                    "memoryUsed": gpu.memoryUsed,
                    "memoryTotal": gpu.memoryTotal,
                    "temperature": gpu.temperature,
                })
        except Exception as gpu_error:
            logging.warning(f"GPU metrics not available: {gpu_error}")

        # System info
        system_info = {
            "cpu_model": platform.processor(),
            "machine": platform.machine(),
            "system": platform.system(),
            "platform": platform.platform(),
        }

        return {
            "cpu": {
                "usage_percent": cpu_usage,
                "per_core_usage": per_core_usage,
                "frequency": cpu_freq,
            },
            "memory": {
                "usage_percent": memory_usage_percent,
                "used": memory_used,
                "total": memory_total,
            },
            "disk": {
                "read_bytes": disk_read,
                "write_bytes": disk_write,
            },
            "gpu": gpu_metrics,
            "system_info": system_info,
        }
    except Exception as e:
        logging.error(f"Error collecting metrics: {e}")
        raise HTTPException(status_code=500, detail="Error collecting hardware metrics")
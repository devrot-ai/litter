param(
    [string]$Video = "data/raw/traffic.mp4",
    [string]$ApiUrl = "http://127.0.0.1:8000",
    [string]$CameraId = "cam-01"
)

.\.venv\Scripts\Activate.ps1
python -m services.inference.run_offline --video $Video --api-url $ApiUrl --camera-id $CameraId

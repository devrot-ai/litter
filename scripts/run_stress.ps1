param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [int]$Requests = 1000,
    [int]$Concurrency = 50,
    [double]$Timeout = 8
)

.\.venv\Scripts\Activate.ps1
python .\scripts\stress_test_api.py --base-url $BaseUrl --requests $Requests --concurrency $Concurrency --timeout $Timeout

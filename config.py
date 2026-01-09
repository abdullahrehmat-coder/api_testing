# config.py

BASE_URL= "https://japp-api.skyelectric.com/api"  # Replace with your cloud URL
TOKEN = "eyJhbGciOiJFUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3OTkzMjAzMzUsImxhbmd1YWdlIjoiZW4iLCJyb2xlIjoiTk9DIiwic3ViIjoiNDZjMWI1NzItZjk2Yi00ZDBmLWJkZmQtNmM2NzkyNjM0ZjE2IiwidHoiOjAsInV0IjowfQ.Aalwc2wvEXpPwupzhjCjK40rs7jR05hkalBAIeGUwvl2iCq-k7bUEm3PjfalgQXf39xS8V9km_-zFCdwCYRnQ-4gAEfOOAnFF641muuASJARaprtSNTSnjSgyIkh9hzNmKesE_NpBATGAi-VQ7LQP-gWIMU0uePlXtqoZ37GkqsQJw1s"

HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {TOKEN}"
}

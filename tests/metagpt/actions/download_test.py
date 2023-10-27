from playwright.async_api import async_playwright
import asyncio


import requests


def download_pdf(url, filename):
    response = requests.get(url)

    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
    else:
        print(f"Failed to download PDF: {response.status_code}")


# 사용 예시
download_pdf(
    "https://invest.kiwoom.com/inv/resource/202309/UploadFile_20230915103535000748.pdf",
    "downloaded_file_2.pdf",
)

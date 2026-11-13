"""Automated demo recording for PaceCraft using Playwright and ffmpeg."""

import os
import shutil
import glob
import subprocess
from playwright.sync_api import sync_playwright

VIDEO_DIR = "/config/Desktop/BuildWithGemini/pacecraft/recordings"
FINAL_VIDEO = "/config/Desktop/BuildWithGemini/pacecraft/pacecraft_demo.mp4"
ARTIFACT_DIR = "/config/.gemini/antigravity/brain/f66ed22b-5c57-4c5d-9a1b-8ccf9df74551"

os.makedirs(VIDEO_DIR, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        record_video_dir=VIDEO_DIR,
        record_video_size={"width": 1280, "height": 800},
    )
    page = context.new_page()

    # 1. Navigate to PaceCraft
    print("Opening PaceCraft...")
    page.goto("http://localhost:8080")
    page.wait_for_timeout(2500)

    # 2. Prompt 1: What the app does best - personalized running pace calculations
    prompt_1 = "I recently ran a 5K race in 21:30. Can you calculate my personalized training paces?"
    print(f"Typing Prompt 1: {prompt_1}")
    page.fill("#input", prompt_1)
    page.wait_for_timeout(1000)
    page.click("button:has-text('Send')")

    # Wait for the response and card to render
    print("Waiting for Prompt 1 reply...")
    page.wait_for_selector(".a2card", timeout=60000)
    page.wait_for_timeout(5000)

    # 3. Prompt 2: Richer query showing off tool call / database lookup
    prompt_2 = "Can you look up your running shoes catalog from Firestore and show specs and pricing?"
    print(f"Typing Prompt 2: {prompt_2}")
    page.fill("#input", prompt_2)
    page.wait_for_timeout(1000)
    page.click("button:has-text('Send')")

    # Wait for second card to render
    print("Waiting for Prompt 2 reply...")
    # Wait until we have at least 2 cards
    page.wait_for_function("document.querySelectorAll('.a2card').length >= 2", timeout=60000)
    page.wait_for_timeout(6000)

    # Scroll up and down slightly to show cards cleanly
    page.evaluate("window.scrollBy(0, 300)")
    page.wait_for_timeout(2000)

    context.close()
    browser.close()

# Locate recorded webm
webm_files = glob.glob(f"{VIDEO_DIR}/*.webm")
if webm_files:
    latest_webm = max(webm_files, key=os.path.getctime)
    print(f"Converting {latest_webm} to MP4...")
    cmd = [
        "ffmpeg", "-y", "-i", latest_webm,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22",
        FINAL_VIDEO
    ]
    subprocess.run(cmd, check=True)
    print(f"Demo video saved to {FINAL_VIDEO}")

    # Also copy to artifacts dir for easy viewing/embedding
    shutil.copy(FINAL_VIDEO, f"{ARTIFACT_DIR}/pacecraft_demo.mp4")
    print(f"Copied to artifact directory: {ARTIFACT_DIR}/pacecraft_demo.mp4")

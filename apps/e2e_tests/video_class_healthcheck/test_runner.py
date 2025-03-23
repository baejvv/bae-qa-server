import json
import logging
import os
import shutil
import subprocess
import requests
import django
import ssl
from django.http import JsonResponse
from django.conf import settings
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from apps.e2e_tests.video_class_healthcheck.slack_template import *

# Django 설정을 명시적으로 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

# ssl 에러 해결
ssl._create_default_https_context = ssl._create_unverified_context

# 팀즈 웹훅
webhook_url = "https://링크 마스킹.webhook.office.com/webhookb2"
# 슬랙 정보
# SLACK_BOT_TOKEN = os.environ['SLACK_BOT_TOKEN']
# Client = WebClient(token=SLACK_BOT_TOKEN, timeout=10)
# channel_id = 'C07EEAS24P8' #alarm-video-class-lesson-status

def run_playwright_test():
    # Playwright 스크립트 파일 경로
    script_path = os.path.join(settings.BASE_DIR, 'apps/e2e_tests/video_class_healthcheck/agora_healthcheck.js')
    # 스크린샷이 저장될 경로
    screenshot_dir = os.path.join(settings.BASE_DIR, 'apps/e2e_tests/video_class_healthcheck/test_screenshots')
    screenshot_path = os.path.join(screenshot_dir, 'screenshot.png')
    # js에 전달할 환경변수 세팅
    env = os.environ.copy()
    env['url'] = os.environ['AGORA_TEST_URL']
    # Node.js를 통해 Playwright 스크립트 실행
    logging.info("Agora 헬스체크 테스트 수행")
    result = subprocess.run(['node', script_path], capture_output=True, text=True, env=env)
    # 실행 결과 확인
    if result.stderr == "":
        logging.info("Agora 헬스체크 테스트 성공")
        result_log = result.stdout
        test_result = "성공"
    else:
        logging.error("Agora 헬스체크 테스트 실패")
        result_log = result.stderr
        test_result = "실패"
    send_teams_message(webhook_url, result_log, test_result)

# 팀즈 웹훅 전송
def send_teams_message(webhook_url, message_text, test_result):
    formatted_text = message_text.replace("\n", "  \n")
    payload = {
        "text": f"## 🚀 agora 헬스체크 결과: {test_result} \n \n ```{formatted_text}```"
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        response.raise_for_status()
        print("Message sent to Teams.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")

# def send_slack_start():
#     try:
#         response = Client.chat_postMessage(
#             channel=channel_id,
#             text="*Agora 헬스체크 테스트 수행중 :loading:*",
#         )
#         return response['ts']
#     except SlackApiError as e:
#         logging.error('테스트 시작 실패: ', e)


# def delete_slack_msg(ts):
#     try:
#         Client.chat_delete(
#             channel=channel_id,
#             ts=ts
#         )
#     except SlackApiError as e:
#         logging.warning('메시지 제거 실패: ', e)


# def send_slack_report(payload, path):
#     try:
#         response = Client.chat_postMessage(
#             channel=channel_id,
#             text="",
#             attachments=payload["attachments"]
#         )
#         ts = response['ts']
#         with open(path, "rb") as screenshot:
#             Client.files_upload(
#                 channels=channel_id,
#                 thread_ts=ts,
#                 file=screenshot,
#                 filename="스크린샷"
#         )
#     except SlackApiError as e:
#         logging.error('리포트 전송 실패: ', e)


def handle_screenshot(screenshot_dir):
    # 스크린샷 디렉토리 내부 파일 삭제
    if os.path.isdir(screenshot_dir):
        try:
            # 디렉토리 내부 파일 및 하위 디렉토리 삭제
            for item in os.listdir(screenshot_dir):
                item_path = os.path.join(screenshot_dir, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
        except Exception:
            logging.warning(f'{screenshot_dir} 내 스크린샷 삭제 실패')


if __name__=="__main__":
    run_playwright_test()
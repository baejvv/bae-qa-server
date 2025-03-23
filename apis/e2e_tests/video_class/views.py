import threading
import json
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from concurrent.futures import ThreadPoolExecutor
from apps.qa_bot import SLACK_VERIFICATION_TOKEN
from apps.e2e_tests import run_playwright_test

'''
엔드포인트를 하나로 관리하기 위한 main 뷰
prod : https://도메인 마스킹/test/video-class
beta : https://도메인 마스킹/test/video-class
'''

class AgoraHealthCheck(APIView):

    executor = ThreadPoolExecutor(max_workers=5)

    def post(self, request, *args, **kwargs):
        if request.data.get('token'):
            data = request.data
            self.executor.submit(self.handle_slack_request, data)
            return Response(status=status.HTTP_200_OK)
        else:
            self.executor.submit(self.is_user_request)
            data = {
                'result': '테스트 시작 성공',
                'description': '실행 결과는 #alarm-video-class-lesson-status 채널에서 확인해주세요.'
            }
            return Response(data, status=status.HTTP_200_OK)

    # 슬랙 요청인지 확인
    def is_slack_request(self, request):
        data = request.data
        if data.get('token'):
            return True
        else:
            return False

    # 슬래시 커맨드 확인
    def handle_slack_request(self, data):

        if data.get('token') != SLACK_VERIFICATION_TOKEN:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if data.get('command') == '/agora':
            agora_th = threading.Thread(target=run_playwright_test(), args=())
            agora_th.start()
            return Response(status=status.HTTP_200_OK)

    # API 직접 요청 시
    def is_user_request(self):
        agora_th = threading.Thread(target=run_playwright_test(), args=())
        agora_th.start()







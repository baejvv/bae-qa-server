import logging
import ssl
import threading
import json
import traceback
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.exception_handler import ThreadExecutionError
from apps.qa_bot import SLACK_VERIFICATION_TOKEN
from apps.qa_bot import slack_method
from apps.qa_bot import create_ticket, make_slack_message
from apps.qa_bot import chat_gpt, channel, project


# ssl 에러 해결
ssl._create_default_https_context = ssl._create_unverified_context

'''
엔드포인트를 하나로 관리하기 위한 main 뷰
prod : https://도메인 마스킹/bot/create-ticket/
beta : https://도메인 마스킹/bot/create-ticket/
'''
class QaBotMainView(APIView):


    def post(self, request, format=None):
        slack_message = request.data
        headers = request.headers

        if headers.get('Platform') == 'JIRA':
            slack_data = request.data
            get_from_jira_th = threading.Thread(target=make_slack_message, args=(slack_data, ))
            get_from_jira_th.start()
            return Response(status=status.HTTP_200_OK)

        if slack_message.get('token'):
            if slack_message.get('token') != SLACK_VERIFICATION_TOKEN:
                return Response(status=status.HTTP_403_FORBIDDEN)

        if slack_message.get('type') == 'url_verification':
            return Response(data=slack_message, status=status.HTTP_200_OK)

        if 'event' in slack_message: # listen all slack event
            event_message = slack_message.get('event')

            # 티켓 등록 로직
            if event_message.get('reaction') == 'jira':
                payload = event_message
                item = payload.get('item')
                # 환경에 따라 channel이 다른 경우 early return
                if channel != item.get('channel'):
                    return Response(status=status.HTTP_200_OK)
                elif slack_method.SlackCustomView(channel, project).is_reaction_presentl(channel, item.get('ts')):
                    return Response(status=status.HTTP_200_OK)
                else:
                    create_ticket_th = threading.Thread(target=create_ticket, args=(payload, ))
                    create_ticket_th.start()
                    return Response(status=status.HTTP_200_OK) # slack 타임아웃 방지를 위한 선 응답


            # chatGPT
            elif event_message.get('type') == 'app_mention' or event_message.get('channel_type') == 'im':
                if 'bot_profile' in event_message: # 봇 메시지는 무시
                    return Response(status=status.HTTP_200_OK)
                gpt_th = threading.Thread(target=chat_gpt, args=(event_message, ))
                gpt_th.start()

                return Response(status=status.HTTP_200_OK)


            return Response(status=status.HTTP_200_OK)
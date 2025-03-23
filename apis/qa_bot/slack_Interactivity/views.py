import json
import threading
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.qa_bot import complete_in_jira, complete_in_slack, modal_process, add_component


'''
슬랙 Interactivity 혹은 숏컷 이벤트 수신
Endpoint
prod : https://도메인 마스킹/bot/interactivity/
beta : https://도메인 마스킹/bot/interactivity/
'''

class InteractivityView(APIView):

    def post(self, request, format=None):

        data = request.data

        # 지라에서 이슈가 완료처리 된 경우
        # user_agent = request.META.get('HTTP_USER_AGENT')
        # if 'Automation for Jira' in user_agent:
        #     ticket_number = data.get('key')
        #     complete_jira_th = threading.Thread(target=complete_in_jira, args=(ticket_number, ))
        #     complete_jira_th.start()

        # 슬랙에서 이슈 완료처리 시도
        if 'payload' in data: # QueryDict를 파이썬dict로 반환
            payload = json.loads(data.dict().get('payload')) # payload의 value를 load
            if payload['type'] == 'block_actions':
                if payload['actions'][0]['action_id'] == 'action_user_select_trigger_btn':
                    complete_slack_th = threading.Thread(target=complete_in_slack, args=(payload, ))
                    complete_slack_th.start()

                elif payload['actions'][0]['action_id'] == 'action_select_comps':
                    add_labels_th = threading.Thread(target=add_component, args=(payload, ))
                    add_labels_th.start()


            elif payload['type'] == 'view_submission':
                complete_slack_modal_interactions_th = threading.Thread(target=modal_process, args=(payload, ))
                complete_slack_modal_interactions_th.start()


        return Response(status=status.HTTP_200_OK)
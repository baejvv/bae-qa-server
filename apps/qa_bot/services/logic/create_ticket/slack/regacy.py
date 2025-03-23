import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from slack_sdk.web.client import WebClient
from slack_sdk.errors import SlackApiError
from apps.qa_bot.services.template import *


json_path = "qa_bot/configs.json"
with open(json_path, 'r') as json_file:
    conf = json.load(json_file)


# Slack
SLACK_BOT_TOKEN = conf['SLACK']['SLACK_BOT_TOKEN']
SLACK_APP_TOKEN = conf['SLACK']['SLACK_APP_TOKEN']
SLACK_VERIFICATION_TOKEN = conf['SLACK']['SLACK_VERIFICATION_TOKEN']
SLACK_SIGNING_SECRET = conf['SLACK']['SLACK_SIGNING_SECRET']
Client = WebClient(token=SLACK_BOT_TOKEN, timeout=10)  # 자원 낭비를 막기 위한 Timeout

# Use Jira API
# pn_list, pk_list = get_jira_project()



class SlackCustomView(APIView):
    # POST 응답이 올 시 모든것을 처리하는 메인 메서드이자 Slack 상호작용의 Rest Endpoint
    def post(self, request, *args, **kwargs):
        global event_message, user, text, channel, ts
        slack_message = request.data

        if slack_message.get('challenge') is not None:
            return Response(status=status.HTTP_200_OK, data=dict(challenge=event_message.get('challenge')))
        # 최초 이모지 발생 혹은 특정 키워드명을 감지하는 로직
        if slack_message.get('event'):
            event_message = slack_message.get('event')
            user = event_message.get('user')
            text = event_message.get('text')
            channel = event_message.get('channel')
            ts = event_message.get('ts')
            try:
                # 이모지 이벤트 감지 시 로직
                if event_message.get('reaction') == 'eyes':
                    # 받은 이벤트가 이모지일 경우 key:type이므로 일부 변수 재정의
                    type = event_message.get('item')
                    channel = type.get('channel')
                    ts = type.get('ts')

                    SlackCustomView.react_event(self) # username return
                    return Response(status=status.HTTP_200_OK)

                # 키워드 감지 시 로직
                elif '!작업' in text:
                    SlackCustomView.react_event(self)
                    return Response(status=status.HTTP_200_OK)

                elif '!이슈' in text:
                    SlackCustomView.react_event(self)
                    return Response(status=status.HTTP_200_OK)

            except SlackApiError as e:
                print(f"이모지/키워드 상호작용 감지 중 에러 발생: {e.response['error']}")
                return Response({"Fail": f"{e.response['error']}"}, status=status.HTTP_400_BAD_REQUEST)


        # payload 응답을 수신한 경우, trigger_id를 추출하여 modal을 띄움
        elif 'payload' in slack_message.dict().keys(): # QueryDict를 파이썬dict로 반환
            payload = json.loads(slack_message.dict().get('payload')) # payload의 value를 load
            if payload['type'] == 'block_actions':
                trigger_id = payload['trigger_id']
                # 드롭다운 업데이트 전 모달 먼저 응답하기 위한 Threading처리, 쓰레드2는 쓰레드1에서 실행
                modal_view = open_reaction_modal()
                try:
                    response, modal_view, view_id = SlackCustomView.run_modal(self, trigger_id, modal_view)
                    if response.status_code == 200:
                        SlackCustomView.update_modal(self, modal_view, view_id, pn_list, pk_list)
                except SlackApiError as e:
                    print("Error opening modal: {}".format(e))
                    return Response({"Fail": f"{e.response['error']}"}, status=status.HTTP_400_BAD_REQUEST)

            # 이슈 등록 버튼을 선택했을 때
            elif payload['type'] == 'view_submission':
                user = payload['user']['id']
                select_values = payload['view']['state']['values']
                ust, usp, uis, uid = select_values.keys()
                selected_type = select_values[ust]['userSelectType']['selected_option']['text']['text']
                selected_project_key = select_values[usp]['userSelectProject']['selected_option']['value']
                inputted_summary = select_values[uis]['userInputSummary']['value']
                inputted_description = select_values[uid]['userInputDescription']['value']
                try:
                    user_name = Client.api_call(api_method='users.info',
                                                params={'token': SLACK_BOT_TOKEN,
                                                        'user': user}
                                                )['user']['real_name']
                    assignee = get_jira_user_id(user_name)['users']['users'][0]['accountId']
                    create_jira_issue(selected_project_key, inputted_summary, inputted_description, selected_type, assignee)
                    return Response(status=status.HTTP_200_OK)

                except Exception as e:
                    print("Error: {}".format(e))
                    return Response({"Fail": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)


    # 정의된 이벤트 수신 시 공개 메시지와 trigger_id를 얻기 위한 private 메시지를 뿌려주고 등록자명을 돌려주는 메서드
    def react_event(self):
        user_name = Client.api_call(api_method='users.info',
                                    params={'token': SLACK_BOT_TOKEN,
                                            'user': user}
                                    )['user']['real_name']
        Client.api_call(api_method='chat.postMessage',
                        params={
                            'channel': channel,
                            'text': send_loading_message(user_name),
                            'thread_ts': ts
                        })
        # payload 이벤트를 받기 위해 이슈 유형 및 프로젝트를 먼저 전달받는 스레드 날림
        Client.chat_postEphemeral(
            channel=channel,
            blocks=get_trigger_button(),
            text='Null',
            user=user,
            thread_ts=ts
        )
        return user_name


    # 모달을 띄워주는 메서드
    def run_modal(self, trigger_id, modal_view):
        res = Client.views_open(
            trigger_id=trigger_id,
            view=modal_view
        )
        view_id = res['view']['id']
        return Response({'ModalOpenSucess'}, status=status.HTTP_200_OK), modal_view, view_id



    # 모달의 뷰를 업데이트 하는 메서드
    def update_modal(self, modal_view, view_id, pnl, pnk):
        # 가져온 list를 드롭다운으로 추가
        for i, value in zip(pnl, pnk):
            modal_view['blocks'][1]['element']['options'].insert(0, {'text': {'type': 'plain_text', 'text': f"{i}"}, 'value': f'{value}'})

        # 로딩문구 교체
        modal_view['blocks'][1]['label']['text'] = "티켓을 등록하실 Jira 프로젝트를 선택해주세요."

        Client.views_update(
            view=modal_view,
            view_id=view_id
        )
        return Response({'ModalUpdateSucess'}, status=status.HTTP_200_OK)

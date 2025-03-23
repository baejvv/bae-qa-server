import os
import re
import requests
from slack_sdk.web.client import WebClient
from slack_sdk.errors import SlackApiError
from apps.qa_bot.services import template
from apps.qa_bot.services.template import *
from apps.qa_bot import SLACK_BOT_TOKEN, SLACK_USER_TOKEN


Client = WebClient(token=SLACK_BOT_TOKEN, timeout=10)
UserClient = WebClient(token=SLACK_USER_TOKEN, timeout=10)


class SlackCustomView():

    '''
    이곳에서 Slack과 통신
    '''

    def __init__(self, channel, project):
        self.channel = channel
        self.project = project

    # 정의된 이모지 추가 시
    def get_real_username(self, item_user, user) -> str:
        username = Client.api_call(api_method='users.info',
                                    params={'token': SLACK_BOT_TOKEN,
                                            'user': user}
                                    )['user']['profile']['display_name']
        item_username = Client.api_call(api_method='users.info',
                                        params={'token': SLACK_BOT_TOKEN,
                                                'user': item_user}
                                        )['user']['profile']['display_name']
        username = re.sub(r"\s.*", "", username)
        item_username = re.sub(r"\s.*", "", item_username)
        return username, item_username

    # reaction이 추가된 ts로 메시지 text get - regacy
    def get_message(self, ts) -> str:
        # Call the conversations.history method using the WebClient
        # The client passes the token you included in initialization
        res = Client.conversations_history(
            channel=self.channel,
            inclusive=True,
            oldest=ts,
            limit=1
        )
        message = res['messages'][0]['text']
        return message

    # 리액션이 찍힌 ts로 text get - new
    def thr_get_message(self, ts) -> str:
        res = Client.conversations_replies(
            channel=self.channel,
            ts=ts,
            inclusive=True,
            oldest=ts,
            limit=1
        )
        msg_info = res['messages'][0]
        summary = msg_info['text']
        # 메시지 내용에 파일이 있는 경우
        if 'files' in msg_info:
            return summary
            # ''' 로직은 정상동작 하지만 사용할 필요 없다고 판단
            # permalink_public 형식 : https://slack-files.com/{team_id}-{file_id}-{pub_secret}
            # 참고 : https://stackoverflow.com/questions/57253156/how-to-use-the-permalink-public-url-of-an-uploaded-image-to-include-it-in-a-mess
            # '''
            # if msg_info['files'][0]['filetype'] == 'jpg' or 'jpeg' or 'png' or 'avi' or 'mov':
            #     # slack_file_pub_secret = re.sub('.*-', '', msg_info['files'][0]['permalink_public'])
            #     # file = msg_info['files'][0]['url_private'] + f'?pub_secret={slack_file_pub_secret}'
            #     try:
            #         file_url = msg_info['files'][0]['url_private']
            #         filename = 'image.jpg'
            #         response = requests.get(file_url, headers={'Authorization': f'Bearer {SLACK_BOT_TOKEN}'})
            #
            #         if response.status_code == 200:
            #             with open(filename, "wb") as f:
            #                 f.write(response.content)
            #                 print('슬랙 이미지 저장 완료. 형식 :', type(f))
            #                 f.close()
            #         return summary, filename
            #     except Exception as e:
            #         print(f'이미지 다운로드 실패: {e}')

        else:
            return summary

    # 최초 로딩 메시지 스레드에 날리기
    def send_loading_message(self, username, ts) -> str:
        d_ts = Client.api_call(api_method='chat.postMessage',
                    params={
                        'channel': self.channel,
                        'text': send_loading_message(username),
                        'thread_ts': ts
                    })
        return d_ts['ts']

    # 이슈 등록 시, 등록된 이슈 링크를 스레드에 날리기
    def send_jira_issue_link(self, user, text, ts, issue_num, comps_options):
        # issue_link = os.environ['JIRA_URL'] + f'jira/software/projects/{project_key}/issues/{issue_num}'
        issue_link = os.environ['JIRA_URL'] + f'browse/{issue_num}'

        res = Client.chat_postMessage(
            channel=self.channel,
            thread_ts=ts,
            text='테스트',
            blocks=send_final_message(user, issue_link, text, issue_num, comps_options)
        )
        return res

        # Client.api_call(api_method='chat.postMessage',
        #           params={
        #               'channel': self.channel,
        #               'text': send_final_message(user) + issue_link + f'\n{text}',
        #               'thread_ts': ts
        #           })

    # 로딩 메시지 삭제
    def delete_loading_message(self, ts):
        Client.chat_delete(
            channel=self.channel,
            ts=ts
        )

    # 슬랙api에러 발생 시 에러전문 메시지 발송
    def send_fail_message(self, ts):
        Client.chat_postMessage(
            channel=self.channel,
            text=f'에러가 발생하여 이슈 등록에 실패하였습니다. 이모지를 다시 찍어주세요.',
            thread_ts=ts
        )

    # 스레드 링크 GET
    def get_thread_link(self, ts) -> str:
        res = Client.chat_getPermalink(
            channel=self.channel,
            message_ts=ts
        )
        return res['permalink']

    # 티켓 등록 시 add reaction
    def add_loading_reaction(self, ts, reaction):
        res = Client.reactions_add(
            channel=self.channel,
            timestamp=ts,
            name=reaction
        )
        return res

    # 로딩 이모지 삭제
    def delete_loading_reaction(self, ts):
        res = Client.reactions_remove(
            channel=self.channel,
            timestamp=ts,
            name='loading'
        )
        return res

    # 티켓 완료 시 add reaction
    def add_done_reaction(self, ts):
        res = Client.reactions_add(
            channel=self.channel,
            timestamp=ts,
            name='complete'
        )
        return res

    # 문자열로 티켓이 등록된 스레드 찾기
    def search_already_thread(self, msg):
        res = UserClient.search_messages(
            query=msg
        )
        return res

    # 티켓 넘버로 티켓이 등록된 스레드 찾기
    def search_already_ticket_thread(self, ticket):
        res = UserClient.search_messages(
         query=ticket
        )
        return res

    # 리액션이 찍힌 글을 스레드 ts로 가져오기
    def get_ts_with_thread_ts(self, reply_ts):
        res = Client.conversations_replies(
            channel=self.channel,
            ts=reply_ts,
        )
        return res

    # 티켓 완료 안내메시지
    def send_jira_complete_message(self, ts, ticket_number):
        res = Client.chat_postMessage(
            channel=self.channel,
            thread_ts=ts,
            text=send_ticket_complete_message(ticket_number)
        )
        return res

    # 티켓 완료 안내메시지(유저이름 포함)
    def send_complete_message(self, ts, slack_user_name, ticket):
        res = Client.chat_postMessage(
            channel=self.channel,
            thread_ts=ts,
            text=template.send_ticket_complete_message_username(slack_user_name, ticket)
        )

    # 티켓 완료 검수 모달 오픈
    def open_complete_modal(self, trigger_id, summary, description, issue, ts):
        res = Client.views_open(
            trigger_id=trigger_id,
            view=template.issue_close_confirm_modal(summary, description, issue, ts)
        )
        return res

    # 이슈가 완료된 경우 메시지 업데이트
    def update_message(self, ts, msg, user):
        Client.chat_update(
            channel=self.channel,
            ts=ts,
            text='test',
            blocks=template.send_update_message(user, msg)
        )

    # 컴포넌트 추가 안내 메시지 전달
    def send_component_add_complete_message(self, ts, component_name, ticket):
        Client.chat_postMessage(
            channel=self.channel,
            text=f'{ticket}에 {component_name} 컴포넌트가 추가되었습니다.',
            thread_ts=ts
        )

    # 중복 이모지 방지
    def is_reaction_presentl(self, channel_id, thread_ts) -> bool:

        try:
            # 특정 메시지의 리액션 가져오기
            response = Client.reactions_get(
                channel=channel_id,
                timestamp=thread_ts
            )
            # 메시지의 리액션 정보에서 특정 리액션이 있는지 확인
            reactions = response['message'].get('reactions', [])
            for reaction in reactions:
                if reaction['name'] == "jira":
                    # 리액션의 개수가 2 이상일 경우 False 반환
                    return reaction['count'] > 1
            return False
        except SlackApiError:
            return False
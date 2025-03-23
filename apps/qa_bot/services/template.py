import json

def send_loading_message(user_name):
    text = f'{user_name}님이 티켓을 등록중입니다 :loading:'
    return text


def send_loading_options():
    text = '티켓이 등록된 Jira 프로젝트의 에픽, 컴포넌트 등을 가져오고 있습니다. :loading:'
    return text


def send_final_message(user, issue_link, text, ticket_number, comps_options):
    # text = f'<@{user}>님이 이슈를 등록하셨습니다:balloon:\n{issue_link}\n{text}'

    text = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f'<@{user}>님이 이슈를 등록하셨습니다.\n\n{issue_link}\n{text}\n\n티켓 완료 처리를 원하시면 완료하기 버튼을 눌러'
                        f'주세요.\n이후 티켓 코멘트에 기재될 완료 메시지를 적어주세요.',
            }
        },
        {
            "type": "section",
            "block_id": ticket_number,
            "text": {
                "type": "mrkdwn",
                "text": "컴포넌트 추가가 필요하시다면? :point_right:"
            },
            "accessory": {
                "type": "static_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "컴포넌트 선택",
                    "emoji": True
                },
                "options": comps_options,
                "action_id": "action_select_comps"
            }
        },
        # 프로젝트 내 스프린트 로직
        # {
        #     "type": "section",
        #     "block_id": "sprint_section",
        #     "text": {
        #         "type": "mrkdwn",
        #         "text": "스프린트 추가가 필요하시다면? :point_right:"
        #     },
        #     "accessory": {
        #         "type": "static_select",
        #         "placeholder": {
        #             "type": "plain_text",
        #             "text": "스프린트 선택"
        #         },
        #         "options": sprint_options,
        #         "action_id": "sprint_select"
        #     }
        # },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": f"{ticket_number} 완료하기",
                        "emoji": True
                    },
                    "style": "primary",
                    "value": ticket_number,
                    "action_id": "action_user_select_trigger_btn"
                }
            ]
        }
    ]

    return text


def send_update_message(user, issue_link):

    text = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*아래 티켓은 완료되었습니다.*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f'<@{user}>님이 이슈를 등록하셨습니다.\n\n{issue_link}',
            }
        }
    ]

    return text


def send_ticket_complete_message(ticket_number):
    text = f'{ticket_number} 티켓이 jira에서 완료처리 되었습니다 :blob_cheer:'
    return text


def send_ticket_complete_message_username(slack_user_name, ticket):
    text = f'<@{slack_user_name}>님이 {ticket}티켓을 완료처리 하였습니다. :blob_cheer:'
    return text


def description_img(attach_url):
    content_desc = {
        "type": "mediaSingle",
        "content": [
            {
                "type": "media",
                "attrs": {
                    "type": "external",
                    "url": attach_url,
                    "width": 2532,
                    "height": 1170
                }
            }
        ]
    }
    return content_desc


def issue_close_confirm_modal(summary, description, issue, ts):
    private_metadata = json.dumps({"issue": issue, "thread_ts": ts})
    text = {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "티켓 처리",
            "emoji": True
        },
        "submit": {
            "type": "plain_text",
            "text": "완료하기",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "취소",
            "emoji": True
        },
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f'티켓 제목 : {summary}'
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f'티켓 내용 : {description}'
                }
            },
            {
                "type": "input",
                "block_id": "inputBlock",
                "element": {
                    "type": "plain_text_input",
                    "multiline": True,
                    "action_id": "userInputText"
                },
                "label": {
                    "type": "plain_text",
                    "text": "티켓 완료 메시지 입력",
                    "emoji": True
                }
            }
        ],
        "private_metadata": private_metadata
    }
    return text


def open_reaction_modal():
    text = {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "dd",
            "emoji": True
        },
        "submit": {
            "type": "plain_text",
            "text": "티켓 등록",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "등록 취소",
            "emoji": True
        },
        "blocks": [
            {
                "type": "input",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "작업, 버그 등..",
                        "emoji": True
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "작업",
                                "emoji": True
                            },
                            "value": "value-0"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "버그",
                                "emoji": True
                            },
                            "value": "value-1"
                        },
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "스토리(미구현)",
                                "emoji": True
                            },
                            "value": "value-2"
                        }
                    ],
                    "action_id": "userSelectType"
                },
                "label": {
                    "type": "plain_text",
                    "text": "티켓의 유형을 선택해주세요.",
                    "emoji": True
                }
            },
            {
                "type": "input",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "직접입력",
                        "emoji": True
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "조금만 기다려주세요.",
                                "emoji": True
                            },
                            "value": "value-0"
                        }
                    ],
                    "action_id": "userSelectProject"
                },
                "label": {
                    "type": "plain_text",
                    "text": "프로젝트 리스트 로딩 중.. :loading:",
                    "emoji": True
                }
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "userInputSummary"
                },
                "label": {
                    "type": "plain_text",
                    "text": "티켓 제목",
                    "emoji": True
                }
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "multiline": True,
                    "action_id": "userInputDescription"
                },
                "label": {
                    "type": "plain_text",
                    "text": "내용 (Jira Ticket Description)",
                    "emoji": True
                }
            }
        ]
    }
    return text


def open_keyword_modal():
    text = {
        "type": "modal",
        "title": {
            "type": "plain_text",
            "text": "My App",
            "emoji": True
        },
        "submit": {
            "type": "plain_text",
            "text": "티켓 등록",
            "emoji": True
        },
        "close": {
            "type": "plain_text",
            "text": "등록 취소",
            "emoji": True
        },
        "blocks": [
            {
                "type": "input",
                "element": {
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "직접입력",
                        "emoji": True
                    },
                    "options": [
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "직접입력",
                                "emoji": True
                            },
                            "value": "value-0"
                        }
                    ],
                    "action_id": "userSelectProject"
                },
                "label": {
                    "type": "plain_text",
                    "text": "프로젝트 리스트 로딩 중.. :loading:",
                    "emoji": True
                }
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "userInputSummary"
                },
                "label": {
                    "type": "plain_text",
                    "text": "티켓 제목",
                    "emoji": True
                }
            },
            {
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "multiline": True,
                    "action_id": "userInputDescription"
                },
                "label": {
                    "type": "plain_text",
                    "text": "내용 (Jira Ticket Description)",
                    "emoji": True
                }
            }
        ]
    }
    return text


def make_select_components(options):

    blocks = [
        {
            "type": "section",
            "block_id": "component_section",
            "text": {
                "type": "mrkdwn",
                "text": "Please select a component:"
            },
            "accessory": {
                "type": "static_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select an item"
                },
                "options": options,
                "action_id": "component_select"
            }
        }
    ]
    return blocks
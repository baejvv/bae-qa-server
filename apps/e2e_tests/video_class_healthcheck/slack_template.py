def success(result_log):
    payload = {
        "attachments": [
            {
                "fallback": "",
                "color": "#36a64f",
                "title": "Agora status 테스트 결과: 성공",  # 굵고 큰 제목 텍스트
                "text": f"```"
                        f"{result_log}"
                        f"```"
            }
        ]
    }
    return payload


def fail(result_log):
    payload = {
        "attachments": [
            {
                "fallback": "",
                "color": "#ee1010",
                "title": "Agora status 테스트 결과: 실패",  # 굵고 큰 제목 텍스트
                "text": f"```"
                        f"{result_log}"
                        f"```"
            }
        ]
    }
    return payload
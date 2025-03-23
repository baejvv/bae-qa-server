import os

def delete_file():
    try:
        if os.path.isfile('image.jpg'): # 만약 이미지가 저장된 경우 이미지 삭제
            os.remove('image.jpg')
            print('이미지 삭제 완료')
    except TypeError:
        print('삭제할 이미지 없음')
        pass


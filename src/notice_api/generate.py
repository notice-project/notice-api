import string

from . import model


def generate_note(trancript: str, usernote: str) -> str:
    # 如果想先用讀檔測試可以用下面這段

    f = open("C:/Users/Homeuser/Desktop/HCI/notice-api/src/notice_api/ml_vs_dl.txt")
    input = []
    ALPHA = string.ascii_letters
    for line in f.readlines():
        if line.startswith(tuple(ALPHA)):
            # print(line)
            input.append(line)
    f.close()

    # 如果要直接把string傳進去用這個
    input = trancript

    outcome = model.gen_model(input, usernote)
    return outcome


# 現在第三條chain還沒弄好 我usernote先隨便傳值進去 之後才會用到這個參數
print(generate_note("1", "2"))

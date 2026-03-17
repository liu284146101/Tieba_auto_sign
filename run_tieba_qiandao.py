from DrissionPage import ChromiumOptions, ChromiumPage
import json
import os
import shutil
import time
import requests

def read_cookie():
    """读取 cookie，优先从环境变量读取"""
    if "TIEBA_COOKIES" in os.environ:
        return json.loads(os.environ["TIEBA_COOKIES"])
    else:
        print("贴吧Cookie未配置！详细请参考教程！")
        return []

def get_level_exp(page):
    """获取等级和经验，如果找不到返回'未知'"""
    try:
        level_ele = page.ele('xpath://*[contains(text(),"等级")]/following-sibling::*', timeout=3)
        level = level_ele.text if level_ele else "未知"
    except:
        level = "未知"
    try:
        exp_ele = page.ele('xpath://*[contains(text(),"经验")]/following-sibling::*', timeout=3)
        exp = exp_ele.text if exp_ele else "未知"
    except:
        exp = "未知"
    return level, exp

if __name__ == "__main__":
    print("程序开始运行")

    # 通知信息
    notice = ''

    co = ChromiumOptions().headless()
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-dev-shm-usage")
    co.set_argument("--disable-gpu")
    chromium_path = shutil.which("chromium-browser")
    if chromium_path:
        co.set_browser_path(chromium_path)

    page = ChromiumPage(co)

    url = "https://tieba.baidu.com/"
    page.get(url)
    page.set.cookies(read_cookie())
    page.refresh()
    page.wait.load_start()
    time.sleep(4)

    over = False
    yeshu = 0
    count = 0

    while not over:
        yeshu += 1
        page.get(f"https://tieba.baidu.com/i/i/forum?&pn={yeshu}")
        page.wait.load_start()
        time.sleep(4)

        for i in range(2, 22):
            try:
                element = page.ele(
                    f'xpath://*[@id="like_pagelet"]/div[1]/div[1]/table/tbody/tr[{i}]/td[1]/a', timeout=3
                )
                tieba_url = element.attr("href")
                name = element.attr("title")
            except:
                msg = f"全部爬取完成！本次总共签到 {count} 个吧..."
                print(msg)
                notice += msg + '\n\n'
                page.close()
                over = True
                break

            page.get(tieba_url)
            page.wait.load_start()
            time.sleep(4)

            # 判断是否已签到（新版匹配）
            is_signed = False
            if page.ele('text():已签到', timeout=2) or page.ele('text():连签', timeout=2):
                is_signed = True

            if is_signed:
                level, exp = get_level_exp(page)
                msg = f"{name}吧：已签到过！等级：{level}，经验：{exp}"
                print(msg)
                notice += msg + '\n\n'
                print("-------------------------------------------------")
            else:
                # ===================== 精准适配你截图的新版签到按钮 =====================
                sign_ele = page.ele('xpath://div[contains(@class,"follow-sign")]//div[text()="签到"]', timeout=5)
                if not sign_ele:
                    sign_ele = page.ele('xpath://div[contains(@class,"operate-btn")]//div[text()="签到"]', timeout=3)
                if not sign_ele:
                    sign_ele = page.ele('text():签到', timeout=3)
                # ======================================================================

                if sign_ele:
                    try:
                        sign_ele.click()
                        time.sleep(3)
                        page.refresh()
                        page.wait.load_start()
                        time.sleep(3)

                        level, exp = get_level_exp(page)
                        msg = f"{name}吧：成功签到！等级：{level}，经验：{exp}"
                        print(msg)
                        notice += msg + '\n\n'
                    except Exception as e:
                        msg = f"{name}吧：签到点击失败：{str(e)}"
                        print(msg)
                        notice += msg + '\n\n'
                else:
                    msg = f"错误！{name}吧：找不到新版签到按钮"
                    print(msg)
                    notice += msg + '\n\n'
                print("-------------------------------------------------")

            count += 1
            page.get(f"https://tieba.baidu.com/i/i/forum?&pn={yeshu}")
            page.wait.load_start()
            time.sleep(3)

    # Server酱通知
    if "SendKey" in os.environ:
        api = f'https://sc.ftqq.com/{os.environ["SendKey"]}.send'
        title = u"贴吧签到信息"
        data = {"text": title, "desp": notice}
        try:
            req = requests.post(api, data=data, timeout=60)
            if req.status_code == 200:
                print("Server酱通知发送成功")
            else:
                print(f"通知失败，状态码：{req.status_code}")
        except Exception as e:
            print(f"通知发送异常：{e}")
    else:
        print("未配置Server酱服务...")

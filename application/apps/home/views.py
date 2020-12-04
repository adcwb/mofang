# import re
# import random
# import json
#
# from flask import current_app
# from application import redis
# from application import jsonrpc
# from application.utils.language.status import APIStatus as status
# from application.utils.language.message import ErrorMessage as message
# from aliyunsdkcore.client import AcsClient
# from aliyunsdkcore.request import CommonRequest
#
#
# @jsonrpc.method("Home.sms")
# def sms(mobile):
#     """发送短信验证码"""
#     # 验证手机
#     if not re.match("^1[3-9]\d{9}$", mobile):
#         print(mobile)
#         return {"errno": status.CODE_VALIDATE_ERROR, "errmsg": message.mobile_format_error}
#
#     # 短信发送冷却时间
#
#     ret = redis.get("int_%s" % mobile)
#     print(ret)
#     if ret is not None:
#         return {"errno": status.CODE_INTERVAL_TIME, "errmsg": message.sms_interval_time}
#     # 生成验证码
#     sms_code = "%06d" % random.randint(0, 999999)
#     # 发送短信
#     # 阿里云短信接口　
#     AccessKeyId = current_app.config.get("AccessKeyId")
#     print("<<<<",AccessKeyId)
#     AccessKeySecret = current_app.config.get("AccessKeySecret")
#     print("<<<<",AccessKeySecret)

#     client = AcsClient(AccessKeyId, AccessKeySecret, 'cn-hangzhou')
#
#     request = CommonRequest()
#     request.set_accept_format('json')
#     request.set_domain('dysmsapi.aliyuncs.com')
#     request.set_method('POST')
#     request.set_protocol_type('https')  # https | http
#     request.set_version('2017-05-25')
#     request.set_action_name('SendSms')
#
#     request.add_query_param('RegionId', "cn-hangzhou")
#     request.add_query_param('PhoneNumbers', mobile)
#     request.add_query_param('SignName', "adcwb")
#     request.add_query_param('TemplateCode', "SMS_205894457")
#     request.add_query_param('TemplateParam', "{\"code\":\"%s\"}" % sms_code)
#
#     response = client.do_action(request)
#     # rest = str(response, encoding='utf-8')
#     rest = eval(response.decode("utf-8"))
#     print(rest)
#
#     rest = {"Message": "OK"}
#     if rest.get("Message") == "OK":
#         pipe = redis.pipeline()
#         pipe.multi()  # 开启事务
#         # 保存短信记录到redis中
#         pipe.setex("sms_%s" % mobile, current_app.config.get("SMS_EXPIRE_TIME"), sms_code)
#         # 进行冷却倒计时
#         pipe.setex("int_%s" % mobile, current_app.config.get("SMS_INTERVAL_TIME"), "_")
#         pipe.execute()  # 提交事务
#         # 返回结果
#         return {"errno": status.CODE_OK, "errmsg": message.ok}
#     else:
#         print(rest.get("Message"))
#         return {"errno": status.CODE_SMS_ERROR, "errmsg": message.sms_send_error}


# ============================================

# 容联云短信接口
import random
import re

from application import jsonrpc
from application import redis
from application.utils.language.message import ErrorMessage as message
from application.utils.language.status import APIStatus as status


@jsonrpc.method(name="Home.sms")
def sms(mobile):
    """发送短信验证码"""
    # 验证手机
    if not re.match("^1[3-9]\d{9}$", mobile):
        return {"errno": status.CODE_VALIDATE_ERROR, "errmsg": message.mobile_format_error}

    # 短信发送冷却时间
    ret = redis.get("int_%s" % mobile)
    if ret is not None:
        return {"errno": status.CODE_INTERVAL_TIME, "errmsg": message.sms_interval_time}

    # 生成验证码
    sms_code = "%06d" % random.randint(0, 999999)
    try:
        from mycelery.sms.tasks import send_sms
        # 异步发送短信
        send_sms.delay(mobile=mobile, sms_code=sms_code)
        # 返回结果
        return {"errno": status.CODE_OK, "errmsg": message.sms_is_send}
    except Exception as e:
        return {"errno": status.CODE_SMS_ERROR, "errmsg": message.sms_send_error}

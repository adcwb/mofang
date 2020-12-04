import json
from application import redis
from flask import current_app
from ronglian_sms_sdk import SmsSDK
from mycelery.main import app, flask_app
from celery.app.task import Task

@app.task(name="send_sms", bind=True)
def send_sms(self, mobile, sms_code):
    """发送短信"""
    try:
        with flask_app.app_context():
            sdk = SmsSDK(
                current_app.config.get("SMS_ACCOUNT_ID"),
                current_app.config.get("SMS_ACCOUNT_TOKEN"),
                current_app.config.get("SMS_APP_ID")
            )
            ret = sdk.sendMessage(
                current_app.config.get("SMS_TEMPLATE_ID"),
                mobile,
                (sms_code, current_app.config.get("SMS_EXPIRE_TIME") // 60)
            )
            result = json.loads(ret)

            if result["statusCode"] == "000000":
                pipe = redis.pipeline()
                pipe.multi()  # 开启事务
                # 保存短信记录到redis中
                pipe.setex("sms_%s" % mobile, current_app.config.get("SMS_EXPIRE_TIME"), sms_code)
                # 进行冷却倒计时
                pipe.setex("int_%s" % mobile, current_app.config.get("SMS_INTERVAL_TIME"), "_")
                pipe.execute()  # 提交事务
            else:
                current_app.log.error("短信发送失败!\r\n%s" % ret)
                raise Exception
    except Exception as exc:
        # 重新尝试执行失败任务
        print(self.request.retries)  # 本次执行的次数
        self.retry(exc=exc, countdown=3, max_retries=5)


"""基于监听器完成任务监听"""



class SMSTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        print('任务执行成功!')
        return super().on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print('任务执行失败!%s' % self.request.retries)
        # 重新尝试执行失败任务，时间间隔:3秒，最大尝试次数：5次
        self.retry(exc=exc, countdown=3, max_retries=5)
        return super().on_failure(exc, task_id, args, kwargs, einfo)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        print('this is after return')
        return super().after_return(status, retval, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        print('this is retry')
        return super().on_retry(exc, task_id, args, kwargs, einfo)


@app.task(name="send_sms2", base=SMSTask)
def send_sms2(mobile, sms_code):
    """发送短信"""
    with flask_app.app_context():
        sdk = SmsSDK(
            current_app.config.get("SMS_ACCOUNT_ID"),
            current_app.config.get("SMS_ACCOUNT_TOKEN"),
            current_app.config.get("SMS_APP_ID")
        )
        ret = sdk.sendMessage(
            current_app.config.get("SMS_TEMPLATE_ID"),
            mobile,
            (sms_code, current_app.config.get("SMS_EXPIRE_TIME") // 60)
        )
        result = json.loads(ret)

        if result["statusCode"] == "000000":
            pipe = redis.pipeline()
            pipe.multi()  # 开启事务
            # 保存短信记录到redis中
            pipe.setex("sms_%s" % mobile, current_app.config.get("SMS_EXPIRE_TIME"), sms_code)
            # 进行冷却倒计时
            pipe.setex("int_%s" % mobile, current_app.config.get("SMS_INTERVAL_TIME"), "_")
            pipe.execute()  # 提交事务
        else:
            current_app.log.error("短信发送失败!\r\n%s" % ret)
            raise Exception


"""
from mycelery.sms.tasks import send_sms2
send_sms2.delay(mobile="13312345678",sms_code="123456")

send_sms.delay(mobile="13928835901",sms_code="123456")
"""

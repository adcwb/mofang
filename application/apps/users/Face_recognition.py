"""
实名认证文件
"""


from aip import AipFace

""" 你的 APPID AK SK """
APP_ID = '23185076'
API_KEY = 'hv1TnBqy5NZYaDkI0zdM7wMA'
SECRET_KEY = 'mW3RHqGsMmIxw2UqyFuaSxfGk4kQUtxs'


client = AipFace(APP_ID, API_KEY, SECRET_KEY)


# image = "取决于image_type参数，传入BASE64字符串或URL字符串或FACE_TOKEN字符串"
image = ""
imageType = "FACE_TOKEN"

""" 调用人脸检测 """
# client.detect(image, imageType);

""" 如果有可选参数 """
options = {}
options["face_field"] = "age,beauty,expression,face_shape,gender,glasses,landmark,landmark72，landmark150，race," \
                        "quality,eye_status,emotion,face_type "
options["max_face_num"] = 1


""" 带参数调用人脸检测 """
client.detect(image, imageType, options)

import pymongo

from urllib import parse

user = parse.quote_plus("root")
pwd = parse.quote_plus("123456")
db = parse.quote_plus("admin")
host = "127.0.0.1"
port = "27017"

# 连接mongodb
mongo = pymongo.MongoClient('mongodb://%s:%s@%s:%s/%s' % (user, pwd, host, port, db))

# 创建数据库
my_db = mongo["test_db"]
# print(mongo.list_database_names())

# 创建文档集
my_collection = my_db["test_collections"]
# print(my_db.list_collection_names())

# 插入一条数据
# document = {
#     "_id": "1", "name": "python", "age": "18", "price": 35.88, "sex": True, "mobile": 17319006602, "money": 123.45}
#
# ret = my_collection.insert_one(document)
# print(ret.inserted_id)

# 插入多条数据

# document_list = [
#     {"_id": "2", "name": "python2", "age": "18", "price": 35.73, "sex": True, "mobile": 17319006602, "money": 13.45},
#     {"_id": "3", "name": "python3", "age": "16", "price": 35.31, "sex": True, "mobile": 13212345677, "money": 34.45},
#     {"_id": "4", "name": "python4", "age": "14", "price": 56.88, "sex": True, "mobile": 13467893345, "money": 66.45},
#     {"_id": "5", "name": "python5", "age": "18", "price": 87.88, "sex": True, "mobile": 17319006602, "money": 123.45},
#     {"_id": "6", "name": "python6", "age": "13", "price": 35.88, "sex": True, "mobile": 13456324567, "money": 123.45},
#     {"_id": "7", "name": "python7", "age": "11", "price": 35.77, "sex": True, "mobile": 13245678333, "money": 123.45},
#     {"_id": "8", "name": "python8", "age": "28", "price": 35.23, "sex": True, "mobile": 17319006602, "money": 123.45},
#     {"_id": "9", "name": "python9", "age": "34", "price": 56.88, "sex": True, "mobile": 17319006602, "money": 123.45},
#     {"_id": "10", "name": "python10", "age": "28", "price": 12.56, "sex": True, "mobile": 17319006602, "money": 123.45},
#     {"_id": "11", "name": "python11", "age": "28", "price": 12.88, "sex": True, "mobile": 17319006602, "money": 123.45},
#     {"_id": "12", "name": "python12", "age": "38", "price": 35.67, "sex": True, "mobile": 17319006602, "money": 123.45},
# ]
#
# ret = my_collection.insert_many(document_list)
# print(ret.inserted_ids)


# 查看一个文档，若值为空则返回None
# ret = my_collection.find_one()
# print(ret)
# {'_id': '1', 'name': 'python', 'age': '18', 'price': 35.88, 'sex': True, 'mobile': 17319006602, 'money': 123.45}

# 查看全部文档，若值为空则返回[]
# for doc in my_collection.find():
#     print(doc)

# 查看文档部分字段，find和find_one的第二个参数表示控制字段的显示隐藏，1为显示，0为隐藏
# for doc in my_collection.find({},{"_id": "0", "name": "1"}):
#     print(doc)
#     {'_id': '1', 'name': 'python'}


# 条件查询
# query = {"age": "18"}  # age = 18
# query = {"age": {"$gt": "18"}}  # age < 18
# for doc in my_collection.find(query, {"_id": "0", "name": "1"}):
#     print(doc)


# 排序显示, 默认从小到大
# for doc in my_collection.find().sort("age"):
#     print(doc)
# for doc in my_collection.find().sort([("age", 1), ("name", -1)]):
#     print(doc)

# 限制查询结果数量
# for doc in my_collection.find().sort("age").limit(5):
#     print(doc)


# 删除单个文档
# query = {"_id": "12"}
# ret = my_collection.delete_one(query)
# print(ret.deleted_count)


# 删除满足某些条件的文档
# query = {"moblie": {"$regex": "^17319"}}
# ret = my_collection.delete_many(query)
# print(ret.deleted_count)


# 查询一条数据出来并删除
# 返回一条数据，如果没有，则返回None
# query = {"name":"python10"}
# document = my_collection.find_one_and_delete(query)
# print(document)


"""更新文档"""
"""按条件更新一个文档的指定数据"""
# query = {"name": "java"}
# upsert = {"$set": {"age": 18}}
# ret = my_collection.update_one(query, upsert)
# print(ret.modified_count)  # 0 表示没有任何修改，1表示修改成功

"""按条件累加/累减指定数值一个文档的指定数据"""
# query = {"name": "java"}
# # upsert = {"$inc": {"age": -1}}  # 累减
# upsert = { "$inc": { "age": 1 } }  # 累加
# ret = my_collection.update_one(query, upsert)
# print(ret.modified_count)


"""更新多条数据"""
# 把所有以"133"开头的手机码号的文档，全部改成15012345678
query = {"mobile": {"$regex": "^173"}}
upsert = {"$set": {"mobile": "13812345678"}}
ret = my_collection.update_many(query, upsert)
print(ret.modified_count)

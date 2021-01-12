from application import redis
from mycelery.main import app,flask_app
from application import mongo

@app.task(name="tree_write",bind=True)
def tree_write(self):
    """允许浇水"""
    try:
        tree_list_water = redis.get("tree_list_water")
        if tree_list_water is None:
            return
        tree_list_water = tree_list_water.decode()
        tree_list = tree_list_water.split(",")[:-1]
        print(tree_list)
        for tree in tree_list:
            treeinfo = tree.split("_")
            query = {"_id": treeinfo[0]}
            user_info = mongo.db.user_info_list.find_one(query)
            user_tree_list = user_info.get("user_tree_list", [])
            # 是否允许浇水
            timer = redis.ttl("user_tree_water_%s" % tree)
            if timer == -2 and user_tree_list[int(treeinfo[1])]['allow_water']== False:
                user_tree_list[int(treeinfo[1])]['allow_water'] = True

            # 是否进入成长期
            timer = redis.ttl("user_tree_growup_%s" % tree)
            if timer == -2 and user_tree_list[int(treeinfo[1])]["status"] == 2:
                if user_tree_list[int(treeinfo[1])]['waters'] > 0:
                    user_tree_list[int(treeinfo[1])]["status"] = 3
                    # tree_list_water_str = "".join(tree_list_water.split(tree + ","))
                    # redis.set("tree_list_water", tree_list_water_str)
            mongo.db.user_info_list.update_one(query, {"$set": {"user_tree_list": user_tree_list}})
    except Exception as exc:
        # 重新尝试执行失败任务
        print(exc)
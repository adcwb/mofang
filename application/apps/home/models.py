from application import db


class User(db.Model):
    __tablename__ = "mf_user"
    id = db.Column(db.Integer, primary_key=True, comment="主键ID")
    name = db.Column(db.String(255), unique=True, comment="账户名")
    password = db.Column(db.String(255), comment="登录密码")
    ip_address = db.Column(db.String(255), index=True, comment="登录IP")

    def __repr__(self):
        return self.name

"""健康数据只读访问（MySQL）。

供"老人健康报告"工具使用，按老人ID + 月份读取：
    tb_older        老人基本信息
    tb_healthyfiles 健康档案（按 createtime 归月）
    tb_internal     内科体检指标（经 healthy_Id 关联档案）
"""
import os
from typing import List, Dict, Any

import pymysql
from pymysql.cursors import DictCursor

from utils.logger_handler import logger

SEX_MAP = {"0": "男", "1": "女"}
MARITAL_MAP = {"0": "未婚", "1": "已婚", "2": "离异"}
EDUCATION_MAP = {"0": "文盲", "1": "小学", "2": "中学", "3": "大学", "4": "硕士", "5": "博士"}


def _connect():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "communitypension"),
        charset="utf8mb4",
        cursorclass=DictCursor,
        connect_timeout=5,
    )


def _query(sql: str, args: tuple = ()) -> List[Dict[str, Any]]:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()


def list_olders(user_id: str = "") -> str:
    """返回老人列表：id-姓名-年龄-病史。优先当前用户名下，其次全部。"""
    rows = []
    if user_id:
        try:
            rows = _query(
                "SELECT id, older_name, older_age, sex, medical_history FROM tb_older "
                "WHERE user_Id = %s AND (del_flag = 0 OR del_flag IS NULL) ORDER BY id",
                (user_id,),
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("按用户查询老人失败：%s", e)
    if not rows:
        rows = _query(
            "SELECT id, older_name, older_age, sex, medical_history FROM tb_older "
            "WHERE (del_flag = 0 OR del_flag IS NULL) ORDER BY id LIMIT 50"
        )
    if not rows:
        return "系统中暂无老人档案"
    lines = []
    for r in rows:
        lines.append(
            f"老人ID:{r['id']} 姓名:{r.get('older_name')} "
            f"年龄:{r.get('older_age')} 性别:{SEX_MAP.get(str(r.get('sex')), '未知')} "
            f"病史:{r.get('medical_history') or '无'}"
        )
    return "\n".join(lines)


def fetch_health_record(older_id: str, month: str) -> str:
    """按老人ID与月份返回健康档案 + 内科指标的结构化文本。"""
    older_id = str(older_id).strip()
    month = str(month).strip()
    if not older_id.isdigit():
        return f"老人ID不合法：{older_id}，请先通过老人列表确认ID"

    older = _query(
        "SELECT id, older_name, older_age, sex, communityCd, medical_history, birthday "
        "FROM tb_older WHERE id = %s AND (del_flag = 0 OR del_flag IS NULL)",
        (older_id,),
    )
    if not older:
        return f"未找到老人（ID={older_id}）"
    o = older[0]

    files = _query(
        "SELECT id, height, weight, nation, native_place, marital_status, work_year, "
        "education_level, career, files, createtime FROM tb_healthyfiles "
        "WHERE older_id = %s AND (del_flag = 0 OR del_flag IS NULL) "
        "AND DATE_FORMAT(createtime, '%%Y-%%m') = %s ORDER BY createtime DESC",
        (older_id, month),
    )

    parts = [
        f"【老人基本信息】姓名：{o.get('older_name')}，年龄：{o.get('older_age')}，"
        f"性别：{SEX_MAP.get(str(o.get('sex')), '未知')}，社区：{o.get('communityCd')}，"
        f"病史：{o.get('medical_history') or '无'}，出生日期：{o.get('birthday')}",
    ]

    if not files:
        parts.append(f"【健康档案】未查询到 {month} 的体检档案")
        return "\n".join(parts)

    for f in files:
        parts.append(
            "【健康档案】时间：{t}，身高：{h}m，体重：{w}kg，民族：{n}，籍贯：{np}，"
            "婚姻：{m}，工作年限：{wy}，文化程度：{edu}，职业：{c}，档案描述：{desc}".format(
                t=f.get("createtime"), h=f.get("height"), w=f.get("weight"),
                n=f.get("nation"), np=f.get("native_place"),
                m=MARITAL_MAP.get(str(f.get("marital_status")), f.get("marital_status")),
                wy=f.get("work_year"),
                edu=EDUCATION_MAP.get(str(f.get("education_level")), f.get("education_level")),
                c=f.get("career"), desc=f.get("files"),
            )
        )
        internals = _query(
            "SELECT heart_rate, blood_pressure, blood_sugar, blood_fat, pulse, "
            "liver_function, renal_function, blood_routine, urinalysis FROM tb_internal "
            "WHERE healthy_Id = %s AND (del_flag = 0 OR del_flag IS NULL) "
            "ORDER BY createtime DESC LIMIT 1",
            (f["id"],),
        )
        if internals:
            i = internals[0]
            parts.append(
                "【内科指标】心率：{hr}，血压：{bp}，血糖：{bs}，血脂：{bf}，脉搏：{p}，"
                "肝功能：{lf}，肾功能：{rf}，血常规：{br}，尿常规：{ua}".format(
                    hr=i.get("heart_rate"), bp=i.get("blood_pressure"), bs=i.get("blood_sugar"),
                    bf=i.get("blood_fat"), p=i.get("pulse"), lf=i.get("liver_function"),
                    rf=i.get("renal_function"), br=i.get("blood_routine"), ua=i.get("urinalysis"),
                )
            )
    return "\n".join(parts)
